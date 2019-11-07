import xlsxwriter as excel

class Excel :
    def __init__(self, path : str, name : str, fileType : str) :
        self.workBook = excel.Workbook(path + name + "." + fileType)

    def addSheet(self, name : str) : 
        return self.workBook.add_worksheet(name)

    #sheet:excel sheet页对象
    #point:数据插入点 (col, row)
    #data:数据 [[(merge_x,merge_y,text,layout_id),...],[...],...]
    #layout:单元格格式 {layout_id: {}}
    def write(self, sheet, point, data, layout) :
        #创建需要的格式
        fm = {0 : None}
        for k, v in layout.items() :
            fm[k] = self.workBook.add_format(v)

        for y in range(0, len(data)) :
            row = data[y]
            py = point[1] + y
            for x in range(0, len(row)) :
                d = row[x]
                if d is None :
                    continue

                if d[0] == 0 and d[1] == 0 :
                    sheet.write(py, point[0] + x, d[2], fm[d[3]])
                else :
                    sheet.merge_range(py, point[0] + x, py + d[1], point[0] + x + d[0], d[2], fm[d[3]])

    def insertPie(self, sheet, name, row, col, sheetname, categories, values) :
        chart = self.workBook.add_chart({'type': 'pie'})
        chart.add_series({
            "categories": "=" + sheetname + "!" + categories,
            "values": "=" + sheetname + "!" + values,
            "name": name
        })

        sheet.insert_chart(row, col, chart)

    def insertColumn(self, sheet, name, row, col, sheetname, categories, values) :
        chart = self.workBook.add_chart({'type': 'column'})
        chart.add_series({
            "categories": "=" + sheetname + "!" + categories,
            "values": "=" + sheetname + "!" + values,
            "name": name
        })

        sheet.insert_chart(row, col, chart)

    def insertTable(self, ttype, sheet, name, row, col, sheetname, categories, values) :
        chart = self.workBook.add_chart({'type': ttype})
        chart.add_series({
            "categories": "=" + sheetname + "!" + categories,
            "values": "=" + sheetname + "!" + values,
            "name": name
        })

        sheet.insert_chart(row, col, chart)

    def close(self) :
        self.workBook.close()
