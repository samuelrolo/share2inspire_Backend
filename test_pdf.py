import sys
import json
import os
from utils.report_pdf import ReportPDFGenerator

# Sample data
report_data = {
    "candidate_profile": {
        "detected_name": "Samuel Rollo",
        "detected_role": "Senior Career Consultant",
        "total_years_exp": "Anos de experiência acumulada: 12",
        "seniority": "Sénior"
    },
    "maturity_and_skills": [
        {"title": "Recrutamento", "metric": "Especialista", "detail": "HR Tech, ATS"}
    ],
    "key_strengths": [
        {"title": "Visão Estratégica", "metric": "Alta", "detail": "Capacidade de antecipar tendências."}
    ],
    "evolution_roadmap": {
        "pdf_details": [
            {
                "title": "Certificação Global",
                "context": "Necessidade de alinhar com padrões internacionais.",
                "actions": ["Estudo de caso A", "Certificação B"]
            }
        ]
    },
    "strategic_feedback": {
        "pdf_details": {
            "market_read": "Mercado em expansão.",
            "what_to_reinforce": "Networking.",
            "what_to_adjust": "Bio do LinkedIn."
        }
    },
    "radar_data": {
        "ats": 85,
        "impact": 90,
        "structure": 75,
        "market_fit": 80,
        "readiness": 88
    },
    "final_verdict": {
        "score": 85
    }
}

try:
    generator = ReportPDFGenerator()
    pdf_bytes = generator.create_pdf(report_data)
    
    if pdf_bytes:
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("PDF generated successfully: test_report.pdf")
    else:
        print("Failed to generate PDF.")
except Exception as e:
    print(f"Error: {e}")
