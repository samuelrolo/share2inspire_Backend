#!/usr/bin/env python3
"""
Script de teste para geração de PDF com análise heurística completa.
"""

import io
import sys
sys.path.insert(0, '/home/ubuntu/share2inspire_Backend')

from utils.analysis import CVAnalyzer
from utils.report_pdf import generate_cv_report

# CV de teste simulado
TEST_CV_TEXT = """
Samuel Rolo
Email: samuel.rolo@email.com
Telefone: +351 912 345 678
LinkedIn: linkedin.com/in/samuelrolo

RESUMO PROFISSIONAL
Gestor de Projetos com mais de 8 anos de experiência em tecnologia e consultoria.
Especializado em transformação digital e implementação de soluções empresariais.

EXPERIÊNCIA PROFISSIONAL

Senior Project Manager | TechCorp Portugal | 2020 - Presente
- Gestão de portfolio de projetos com orçamento total de €2M
- Liderança de equipa de 12 profissionais
- Implementação de metodologias ágeis (Scrum, Kanban)
- Redução de 30% no tempo de entrega de projetos

Project Manager | Consulting Group | 2017 - 2020
- Gestão de projetos de transformação digital
- Coordenação com stakeholders C-level
- Implementação de SAP em 3 empresas do setor financeiro

Analista de Sistemas | StartupTech | 2015 - 2017
- Desenvolvimento de soluções em Python e JavaScript
- Análise de requisitos e documentação técnica
- Suporte a equipas de desenvolvimento

FORMAÇÃO ACADÉMICA

Mestrado em Gestão de Sistemas de Informação | ISCTE | 2015
Licenciatura em Engenharia Informática | Universidade de Lisboa | 2013

CERTIFICAÇÕES
- PMP - Project Management Professional
- Scrum Master Certified
- ITIL Foundation

COMPETÊNCIAS TÉCNICAS
- Gestão de Projetos: MS Project, Jira, Asana
- Metodologias: Scrum, Kanban, Waterfall, Prince2
- Tecnologias: Python, SQL, Power BI, SAP
- Cloud: AWS, Azure

IDIOMAS
- Português: Nativo
- Inglês: Fluente (C1)
- Espanhol: Intermédio (B1)
"""

def main():
    print("=" * 60)
    print("TESTE DE GERAÇÃO DE PDF - ANÁLISE HEURÍSTICA COMPLETA")
    print("=" * 60)
    
    # Criar analyzer
    analyzer = CVAnalyzer()
    
    # Criar stream do CV de teste
    cv_stream = io.BytesIO(TEST_CV_TEXT.encode('utf-8'))
    
    # Executar análise
    print("\n[1] Executando análise heurística...")
    analysis_data = analyzer._heuristic_analysis(cv_stream, "test_cv.txt", "Project Manager", "Senior")
    
    # Verificar campos principais
    print("\n[2] Verificando campos da análise...")
    
    required_sections = [
        'candidate_profile',
        'global_summary', 
        'executive_summary',
        'diagnostic_impact',
        'content_structure_analysis',
        'ats_digital_recruitment',
        'skills_differentiation',
        'strategic_risks',
        'languages_analysis',
        'education_analysis',
        'phrase_improvements',
        'pdf_extended_content',
        'priority_recommendations',
        'executive_conclusion',
        'radar_data'
    ]
    
    missing = []
    for section in required_sections:
        if section in analysis_data:
            print(f"  ✓ {section}")
        else:
            print(f"  ✗ {section} - EM FALTA!")
            missing.append(section)
    
    if missing:
        print(f"\n[ERRO] Secções em falta: {missing}")
        return
    
    # Verificar dados do candidato
    print("\n[3] Dados do candidato extraídos:")
    profile = analysis_data.get('candidate_profile', {})
    print(f"  Nome: {profile.get('detected_name', 'N/A')}")
    print(f"  Experiência: {profile.get('total_years_exp', 'N/A')}")
    print(f"  Função: {profile.get('detected_role', 'N/A')}")
    print(f"  Senioridade: {profile.get('seniority', 'N/A')}")
    print(f"  Setor: {profile.get('detected_sector', 'N/A')}")
    print(f"  Formação: {profile.get('education_level', 'N/A')}")
    print(f"  Skills: {profile.get('key_skills', [])}")
    
    # Verificar scores
    print("\n[4] Scores (radar_data):")
    radar = analysis_data.get('radar_data', {})
    for key, value in radar.items():
        print(f"  {key}: {value} (x5 = {value * 5})")
    
    # Gerar PDF
    print("\n[5] Gerando PDF...")
    try:
        pdf_buffer, filename = generate_cv_report(analysis_data)
        
        # Salvar PDF
        output_path = f"/home/ubuntu/{filename}"
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.read())
        
        print(f"  ✓ PDF gerado com sucesso: {output_path}")
        
        # Verificar tamanho
        import os
        size = os.path.getsize(output_path)
        print(f"  Tamanho: {size / 1024:.1f} KB")
        
    except Exception as e:
        print(f"  ✗ Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    main()
