FROM python:3.13-slim

WORKDIR /app

# xhtml2pdf is pure-Python (built on ReportLab), so unlike WeasyPrint it
# needs no Cairo/Pango/GDK-Pixbuf system libraries at all. All that's left
# here is a decent Unicode-capable font set for the generated PDFs/DOCX
# logo, plus the small build deps Pillow occasionally wants on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]