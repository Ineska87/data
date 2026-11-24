import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const bundleRequire = createRequire(path.join(path.dirname(process.execPath), "..", "node_modules", "load.cjs"));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(bundleRequire.resolve("@oai/artifact-tool")));
const work = path.dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(await fs.readFile(path.join(work, "workbook_input.json"), "utf8"));
const out = process.argv[2];
const workbook = Workbook.create();
const palette = { ink: "#243044", header: "#283E56", faint: "#F2F5F8", muted: "#50637A", total: "#E0EBF5" };
const compactFractions = new Set(["Precyzja", "Czułość", "Trafność"]);
const tableStart = 3;

function linesFor(value, width) {
  if (value == null || typeof value === "number") return 1;
  return String(value).split("\n").reduce((n, line) => n + Math.max(1, Math.ceil(line.length / (width * 0.96))), 0);
}

for (const table of data) {
  const sheet = workbook.worksheets.add(table.name);
  sheet.showGridLines = false;
  const widthCount = table.columns.length;
  const bottom = tableStart + table.rows.length + 1;
  const tableRange = sheet.getRangeByIndexes(tableStart, 0, table.rows.length + 1, widthCount);
  const widths = table.columns.map((column, i) => {
    const lengths = [column.length + 2, ...table.rows.map(r => (typeof r[i] === "string" ? r[i].length + 2 : 11))];
    return Math.min(widthCount > 13 ? 47 : 62, Math.max(12, Math.max(...lengths)));
  });
  for (let i = 0; i < widthCount; i++) {
    sheet.getRangeByIndexes(0, i, 1, 1).format.columnWidth = widths[i];
  }
  tableRange.values = [table.columns, ...table.rows];
  tableRange.format.font.name = "Arial";
  tableRange.format.font.size = 10;
  tableRange.format.font.color = palette.ink;
  tableRange.format.verticalAlignment = "center";
  tableRange.format.wrapText = true;

  const headline = sheet.getRangeByIndexes(1, 0, 1, Math.min(7, widthCount));
  headline.merge();
  sheet.getRange("A2").values = [[table.title]];
  headline.format.font.name = "Arial";
  headline.format.font.bold = true;
  headline.format.font.size = 15;
  headline.format.font.color = palette.ink;
  headline.format.rowHeight = 24;
  sheet.getRange("A3").format.rowHeight = 8;

  const header = sheet.getRangeByIndexes(tableStart, 0, 1, widthCount);
  header.format.fill = palette.header;
  header.format.font.color = "#FFFFFF";
  header.format.font.bold = true;
  header.format.horizontalAlignment = "center";
  header.format.rowHeight = 31;
  for (let j = 0; j < table.rows.length; j++) {
    const row = table.rows[j];
    const rowRange = sheet.getRangeByIndexes(tableStart + j + 1, 0, 1, widthCount);
    const maxLines = Math.max(...row.map((v, i) => linesFor(v, widths[i])));
    rowRange.format.rowHeight = Math.min(390, Math.max(21, maxLines * 15 + 7));
    if (maxLines > 1) rowRange.format.verticalAlignment = "top";
    if (j % 2 === 1) rowRange.format.fill = palette.faint;
    if (row[0] === "Łącznie" || row[1] === "Ogółem") {
      rowRange.format.fill = palette.total;
      rowRange.format.font.bold = true;
    }
  }
  for (let c = 0; c < widthCount; c++) {
    const column = table.columns[c];
    const cells = table.rows.map(r => r[c]).filter(v => v !== null);
    if (cells.some(v => typeof v === "number")) {
      const range = sheet.getRangeByIndexes(tableStart + 1, c, table.rows.length, 1);
      const format = compactFractions.has(column) ? "0.0%" : /^p\b/i.test(column) ? "0.0000"
        : (cells.some(v => typeof v === "number" && !Number.isInteger(v))) ? "0.000;-0.000;0.000" : "0";
      range.setNumberFormat(format);
      if (table.id === "Tabela_3_modele") {
        table.rows.forEach((row, j) => {
          const v = row[c];
          if (typeof v === "number") {
            sheet.getCell(tableStart + 1 + j, c).setNumberFormat(Number.isInteger(v) ? "0" : "0.0000;-0.0000;0.0000");
          }
        });
      }
    }
  }
  if (table.id === "Tabela_4_olefiny_iii") sheet.freezePanes.freezeColumns(3);
  else if (table.id === "Tabela_2_car" || table.id === "Tabela_2b_testy") sheet.freezePanes.freezeColumns(2);
  else if (table.rows.length > 14) sheet.freezePanes.freezeRows(tableStart + 1);
  if (table.note) {
    const note = sheet.getRangeByIndexes(bottom + 1, 0, 1, widthCount);
    note.merge();
    sheet.getCell(bottom + 1, 0).values = [[table.note]];
    note.format.font.name = "Arial";
    note.format.font.size = 9;
    note.format.font.italic = true;
    note.format.font.color = palette.muted;
    note.format.wrapText = true;
    note.format.rowHeight = 31;
  }
}
workbook.recalculate();
const file = await SpreadsheetFile.exportXlsx(workbook);
await file.save(out);
for (const key of ["1b", "2 ", "3 ", "4 "]) {
  const table = data.find(d => d.name.startsWith(key));
  if (!table) continue;
  const sheet = workbook.worksheets.getItem(table.name);
  const last = sheet.getRangeByIndexes(0, Math.min(8, table.columns.length) - 1, 1, 1).address.split("!").pop().replace(/\d+/g, "");
  const preview = await workbook.render({ sheetName: table.name, range: `A1:${last}${Math.min(11, 4 + table.rows.length)}`,
    scale: 0.9, format: "png" });
  await fs.writeFile(path.join(work, `preview_${key.trim()}.png`),new Uint8Array(await preview.arrayBuffer()));
}
