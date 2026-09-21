# Digital Grievance & Notice Board System

Hey there! Welcome to the repository for the Digital Grievance & Notice Board System. 

## The Problem It Solves

Traditional methods of filing complaints with local authorities often involve long queues, lost paperwork, and a lack of transparency. Citizens struggle to track the status of their grievances, and municipalities find it difficult to manage and prioritize issues efficiently. This system solves that problem by providing a centralized, digital platform. It brings transparency to the process, allowing citizens to easily report issues from anywhere and track them in real-time, while giving local authorities the tools they need to organize, manage, and resolve complaints effectively.

## What it does

- **Citizen Portal**: Users can sign up, submit grievances categorized by department (e.g., Ward Office Services, Roads & Infrastructure, Health Services), and track the real-time status of their complaints.
- **Staff/Admin Dashboard**: Authorized personnel can review grievances, update their status (e.g., Pending, In Progress, Resolved), and manage public notices.
- **Automated Document Generation**: The system automatically generates downloadable PDF and DOCX reports for grievances and notices, making record-keeping a breeze.

## Tech Stack

This project is built using:
- **Backend:** Python and Django (v5.1.x)
- **Frontend:** HTML, CSS, JavaScript (styled with Tailwind CSS, based on utility classes in the code)
- **Document Generation:** 
  - `xhtml2pdf` & `reportlab` for rendering PDFs directly from HTML templates.
  - `docxtpl` & `python-docx` for populating Word document templates.
- **Database:** SQLite (default for development, easily swappable to PostgreSQL)

## Getting Started

If you want to run this locally, follow these steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Saurav-T/digital-grievance-system.git
   cd digital-grievance-system
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```
   Open up `http://127.0.0.1:8000` in your browser, and you should be good to go!

## Notes

- Make sure you have `Pillow` installed properly, as it's required for handling profile pictures and embedding raster images in the PDF exports.
- I've opted for `xhtml2pdf` for PDF generation because it's pure Python and doesn't require complex system-level dependencies (like Cairo or Pango) which makes deploying in Docker much easier.

## Contributing

Feel free to fork this, open issues, or submit PRs if you find bugs or want to add new features. Any contributions are always appreciated!

---
**Created by the Team:**
- Nabin Adhikari
- Saurav Tamrakar
- Anush Pote
- Hariom Gautam
- Paban Bhandari
