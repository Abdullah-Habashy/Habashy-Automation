import openpyxl

file_path = r"e:\HABASHY\Python Codes\freepik_test_prompts.xlsx"

wb = openpyxl.Workbook()
sheet = wb.active
sheet.title = "Prompts"

# Add Header
sheet["A1"] = "Prompt"

# Add Sample Prompts
prompts = [
    "A futuristic city with flying cars at sunset, cyberpunk style",
    "A cute cat astronaut floating in space, digital art",
    "A serene mountain landscape with a lake, oil painting style",
    "A delicious gourmet burger with cheese and lettuce, food photography"
]

for i, prompt in enumerate(prompts, start=2):
    sheet[f"A{i}"] = prompt

wb.save(file_path)
print(f"Created Excel file at: {file_path}")
