# ExamApp

Aplicación simple para gestionar preguntas de exámenes.

## Requisitos
- Python 3
- Dependencias: `pandas`, `openpyxl`, `pdfplumber`

Instala las dependencias con:

```bash
pip install pandas openpyxl pdfplumber
```

## Uso

### Inicializar la base de datos
```bash
python examapp.py init-db
```

### Importar preguntas desde Excel
El archivo debe contener las columnas: `level`, `subject`, `text`, `option1`, `option2`, `option3`, `option4`, `correct`, `explanation`.

```bash
python examapp.py import-excel preguntas.xlsx
```

### Importar preguntas desde un PDF
Se espera un formato sencillo:

```
1. Pregunta...
A) opción 1
B) opción 2
C) opción 3
D) opción 4
Answer: B
Explanation: explicación de la respuesta
```

```bash
python examapp.py import-pdf guia.pdf --level secundaria --subject matematicas
```

### Evaluar a una persona

```bash
# Examen general de 5 preguntas
python examapp.py evaluate

# Examen de 10 preguntas solo de matemáticas
python examapp.py evaluate --subject matematicas --num 10
```
