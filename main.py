import os
import re
import csv
from PyPDF2 import PdfReader
from pdfquery import PDFQuery

def readScoreSheet(file):
    reader = PdfReader(file)
    first_page = reader.pages[0]
    text = first_page.extract_text()

    game_no = re.findall("Comissão Estadual de Arbitragem de Futebol - CEAF Jogo: (.*) /", text)
    if game_no:
        game_no = game_no[0]
    else:
        game_no = "N/A"

    match = re.findall("Jogo: (.*) X (.*)", text)
    if match:
        home_team = match[0][0]
        away_team = match[0][1]
    else:
        home_team = "N/A"
        away_team = "N/A"

    final_result = re.findall("Resultado Final: (.*) X (.*)", text)
    if final_result:
        home_score = final_result[0][0]
        away_score = final_result[0][1]
    else:
        home_score = "N/A"
        away_score = "N/A"
    
    venue = re.search("Estádio: (.*) / (.*)", text)
    if venue is not None:
        venue = venue.group(0).split(':')[1].strip()
    else:
        venue = "N/A"
    
    return [game_no, home_team, home_score, away_team, away_score, venue]

def readFinancial(file, tmpFile = 'tmp/tmp.xml'):
    pdf = PDFQuery(file)
    pdf.load()
    pdf.tree.write(tmpFile, pretty_print = True)
    totals_line = pdf.pq('LTTextBoxHorizontal:contains("TOTAIS ")')[0].layout
    totals_fp1 = round(totals_line.bbox[1], 3)
    totals_fp2 = round(totals_line.bbox[3], 3)
    net_income_line = pdf.pq('LTTextBoxHorizontal:contains("RENDA LÍQUIDA (RECEITA - DESPESA) ")')[0].layout
    net_income_fp1 = round(net_income_line.bbox[1], 3)
    net_income_fp2 = round(net_income_line.bbox[3], 3)
    with open(tmpFile, 'r') as file:
        data = file.read()
        game_no_patten = "index=\"\d+\">(\d+)/\d{4} </LTTextBoxHorizontal>"
        game_no = re.findall(game_no_patten, data)
        if game_no:
            game_no = game_no[0]
        else:
            game_no = "N/A"

        attendance_pattern = "bbox=\"\[\d{1,3}.\d{1,3}, " + str(totals_fp1) + ", \d{1,3}.\d{1,3}, " + str(totals_fp2) + "\]\" index=\"\d+\">(\d+) <\/LTTextBoxHorizontal>"
        attendance = re.findall(attendance_pattern, data)
        if attendance:
            attendance = attendance[-1]
        else:
            attendance = "N/A"
        
        income_pattern = "bbox=\"\[\d{1,3}.\d{1,3}, " + str(totals_fp1) + ", \d{1,3}.\d{1,3}, " + str(totals_fp2) + "\]\" index=\"\d+\">(\d*.?\d{1,3},\d{2}) <\/LTTextBoxHorizontal>"
        income = re.findall(income_pattern, data)
        if income:
            income = "R$ " + income[0]
        else:
            income = "N/A"
        
        net_income_pattern = "bbox=\"\[\d{1,3}.\d{1,3}, " + str(net_income_fp1) + ", \d{1,3}.\d{1,3}, " + str(net_income_fp2) + "\]\" index=\"\d+\">(-?\d*.?\d{1,3},\d{2}) <\/LTTextBoxHorizontal>" 
        net_income = re.findall(net_income_pattern, data)
        if net_income:
            net_income = "R$ " + net_income[-1]
        else:
            net_income = "N/A"
        
    return [game_no, attendance, income, net_income]

def saveCSV(header, data, output_file):
    with open(output_file, 'w', encoding='UTF8', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(header)
        writer.writerows(data)
    print(output_file + " successfully created.")

if __name__ == "__main__":
    print("Reading scoresheet directory...")
    scoresheet_dir = os.getcwd() + '/scoresheet'
    scoresheet_files = os.listdir(scoresheet_dir)
    print("Found " + str(len(scoresheet_files)) + " file(s).")

    print("Reading financial directory...")
    financial_dir = os.getcwd() + '/financial'
    financial_files = os.listdir(financial_dir)
    print("Found " + str(len(financial_files)) + " file(s).")

    data_scoresheet = []
    financial_data = []

    for file in scoresheet_files:
        if file[-3:] == 'pdf':
            print("Reading " + file + "...")
            data_scoresheet.append(readScoreSheet(scoresheet_dir + '/' + file))
        else:
            print("Only PDF supported: " + file)

    for file in scoresheet_files:
        if file[-3:] == 'pdf':
            print("Reading " + file + "...")
            financial_data.append(readFinancial(financial_dir + '/' + file))
        else:
            print("Only PDF supported: " + file)


    if data_scoresheet:
        scoresheet_output = 'output/scoresheet.csv'
        print("Creating " + scoresheet_output + "...")
        header_scoresheet = ["Partida", "Mandante", "Gols Mandante", "Visitante", "Gols Visitante", "Estádio"]
        saveCSV(header_scoresheet, data_scoresheet, scoresheet_output)
    else:
        print("Scoresheet data not found")

    if financial_data:
        financial_output = 'output/financial.csv'
        print("Creating " + financial_output + "...")
        header_financial = ["Partida", "Público", "Renda Bruta", "Renda Líquida"]
        saveCSV(header_financial, financial_data, financial_output)
    else:
        print("Finacial data not found")

    print("Execution finished")
