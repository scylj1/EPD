from epo_ops import Client
from epo_ops.models import Docdb, Epodoc
import xml.etree.ElementTree as ET
import json
import os
import argparse


def retrieve_meta(client, publication_number):

    response = client.published_data(
        reference_type='publication',  
        input=Epodoc(publication_number),
        endpoint='biblio ', 
    )

    xml_data = response.text

    root = ET.fromstring(xml_data)
    # Namespaces required for querying
    namespaces = {
        '': 'http://www.epo.org/exchange',  # Default namespace
        'ops': 'http://ops.epo.org',       # Namespace for elements prefixed with 'ops'
        'xlink': 'http://www.w3.org/1999/xlink'  # Namespace for elements prefixed with 'xlink'
    }

    # Searching for the 'exchange-documents' element
    exchange_documents = root.find('exchange-documents', namespaces)
    results = []
    
    # Check if we found the element and print information
    if exchange_documents is not None:
        # If you want to print details of each 'exchange-document'
        for doc in exchange_documents:
             
            data = {
                "publication_number": "",
                "title": "",
                "kind_code": "",
                "date_published": "",
                "main_cpci_label": "",
                "cpci_labels": [],
                "main_ipcr_label": "",
                "ipcr_labels": [],
                "family_id": "",
                "application_reference": "", 
                "applicants": [],
                "inventors": [],
                "citations": [], 
                "abstract": "",
            }
            # Document attributes
            data['family_id'] = doc.get('family-id')
            data['publication_number'] = f"{doc.get('country')}{doc.get('doc-number')}"
            data['kind_code'] = doc.get('kind')
            
            # Dive into bibliographic data
            biblio_data = doc.find('.//bibliographic-data', namespaces)
            if biblio_data:
                # Extract publication references
                pub_refs = biblio_data.findall('.//publication-reference/document-id', namespaces)
                for pub_ref in pub_refs:
                    date = pub_ref.find('.//date', namespaces)
                    if date is not None:
                        data['date_published'] = date.text

                # Extract IPC classifications
                ipc_classes = biblio_data.findall('.//classifications-ipcr/classification-ipcr', namespaces)
                for num, ipc_class in enumerate(ipc_classes):
                    if num == 4:
                        break
                    ipc_text = ipc_class.find('.//text', namespaces)
                    if ipc_text is not None:
                        txt = ipc_text.text.replace(" ", "")
                        if txt[-2:] == "AI":
                            txt = txt[:-2]

                        data['ipcr_labels'].append(txt)
                        if num == 0:
                            data['main_ipcr_label'] = txt

                # Extract patent classifications details
                patent_classes = biblio_data.findall('.//patent-classifications/patent-classification', namespaces)
                count = 0
                for patent_class in patent_classes:
                    generating_office = patent_class.find('.//generating-office', namespaces)
                    if generating_office is not None and generating_office.text == 'EP':
                        section = patent_class.find('.//section', namespaces)
                        clazz = patent_class.find('.//class', namespaces)
                        subclass = patent_class.find('.//subclass', namespaces)
                        main_group = patent_class.find('.//main-group', namespaces)
                        subgroup = patent_class.find('.//subgroup', namespaces)

                        # Ensure all parts are present before creating the output string
                        if section is not None and clazz is not None and subclass is not None and main_group is not None and subgroup is not None:
                            classification_string = f"{section.text} {clazz.text} {subclass.text} {main_group.text} / {subgroup.text}".replace(" ", "")
                            # print(f"CPC Classification:{classification_string}")
                            data['cpci_labels'].append(classification_string)
                            if count == 0:
                                data['main_cpci_label'] = classification_string
                            count += 1
                            if count == 4:
                                break
                
                # Applicants
                epodoc_applicants = biblio_data.findall('.//applicants/applicant[@data-format="epodoc"]/applicant-name/name', namespaces)
                for applicant in epodoc_applicants:
                    # print(f"EPodoc Applicant: {applicant.text}")
                    data['applicants'].append(applicant.text.replace('\u2002', ' '))

                # Inventors
                inventors = biblio_data.findall('.//inventors/inventor[@data-format="epodoc"]/inventor-name/name', namespaces)
                for inventor in inventors:
                    # print(f"Inventor: {inventor.text}")
                    data['inventors'].append(inventor.text.replace('\u2002', ' '))

                # Application reference
                application_references = biblio_data.findall('.//application-reference/document-id[@document-id-type="epodoc"]/doc-number', namespaces)
                for reference in application_references:
                    #print(f"Application reference: {reference.text}")
                    data['application_reference'] = reference.text

                # Extract invention titles
                title = biblio_data.find('.//invention-title[@lang="en"]', namespaces)
                if title is not None:
                    data['title'] = title.text

                # extract citations
                citations = []
                for citation in biblio_data.findall('.//references-cited/citation', namespaces):
                    citation_dict = {
                        'cited_phase': citation.get('cited-phase'),
                        'cited_by': citation.get('cited-by'),
                        'source': "",
                        'text': "", 
                        'document_number': "", 
                        'category': "",
                        'related_claims': "",
                        'related_passages': [],

                    }
                    
                    # patent citation
                    patcit = citation.find('.//patcit', namespaces)
                    if patcit is not None:
                        citation_dict['source'] = 'patcit'
                        doc_number = patcit.find('.//document-id[@document-id-type="epodoc"]/doc-number', namespaces)
                        citation_dict['document_number'] = doc_number.text

                    category = citation.find('.//category', namespaces)
                    if category is not None:
                        citation_dict['category'] = category.text
                    
                    rel_claims = citation.find('.//rel-claims', namespaces)
                    if rel_claims is not None:
                        citation_dict['related_claims'] = rel_claims.text

                    rel_passages = citation.findall('.//rel-passage/passage', namespaces)
                    for passage in rel_passages:
                        citation_dict['related_passages'].append(passage.text)

                    # non-patent literature citation
                    nplcit = citation.find('.//nplcit', namespaces)
                    if nplcit is not None:     
                        citation_dict['source'] = 'nplcit'                   
                        citation_dict['text'] = nplcit.find('.//text', namespaces).text if nplcit.find('.//text', namespaces) is not None else ""

                    citations.append(citation_dict)

                data['citations'] = citations
                
            abstract_data = doc.find('.//abstract[@lang="en"]/p', namespaces)      
            if abstract_data is not None:
                data['abstract'] = abstract_data.text
                # print(abstract_data.text)
                          
            results.append(data) 
                           
    else:
        print("No 'exchange-documents' element found.")

    return results

def retrieve_abstract(client, publication_number, kind_code):
    
    abstract = ""
    try:
        response = client.published_data(
            reference_type='publication',  
            input=Epodoc(publication_number, kind_code),
            endpoint='abstract', 
        )

        xml_data = response.text
        # print(xml_data)

        root = ET.fromstring(xml_data)
        namespaces = {
            '': 'http://www.epo.org/exchange',  # Default namespace
            'ops': 'http://ops.epo.org',       # Namespace for elements prefixed with 'ops'
            'xlink': 'http://www.w3.org/1999/xlink'  # Namespace for elements prefixed with 'xlink'
        }
        # Searching for the 'exchange-documents' element
        exchange_document = root.find('.//exchange-document', namespaces)

        # Check if we found the element and print information
        abstract = ''
        if exchange_document is not None:    
            abstract_data = exchange_document.find('.//abstract[@lang="en"]/p', namespaces)
            if abstract_data is not None:
                abstract = abstract_data.text
                # print(abstract_data.text)
            else:
                abstract = "not available"
                
    except Exception as e:
        print(e)
    
    return abstract 

def retrieve_claim_description(client, publication_number, kind_code): 
    
    try:
        response = client.published_data(
            reference_type='publication',  
            input=Epodoc(publication_number, kind_code),
            endpoint='claims', 
        )

        xml_data = response.text
        root = ET.fromstring(xml_data)

        namespaces = {'ftxt': 'http://www.epo.org/fulltext'}  
        english_claims = root.findall('.//ftxt:claims[@lang="EN"]/ftxt:claim/ftxt:claim-text', namespaces)
        en = ""
        for claim in english_claims:
            en += claim.text + " "
        en = en.replace('\n', '')
  
    except Exception as e:
        en = ""    
    
    try:
        response = client.published_data(
            reference_type='publication',  
            input=Epodoc(publication_number, kind_code),
            endpoint='description', 
        )

        xml_data = response.text
        
        root = ET.fromstring(xml_data)
        namespaces = {
            '': 'http://www.epo.org/fulltext'  
        }

        paragraphs = root.findall('.//description[@lang="EN"]/p', namespaces)

        combined_text = ' '.join(p.text for p in paragraphs if p.text)
        description = combined_text.replace('\n', '')
        
    except Exception as e:
        description = ""
            
    return en, description

if __name__=='__main__':

    parser = argparse.ArgumentParser(description="retrieve data")
    parser.add_argument("--key", type=str, default=None) 
    parser.add_argument("--secret", type=str, default=None) 
    args = parser.parse_args()
    
    client = Client(
        key=args.key,
        secret=args.secret,

    )
    
    meta = retrieve_meta(client, "EP3721815")
    # print(meta)
    
    abstract = retrieve_abstract(client, "EP3721815", "A2")
    # print(abstract)
    
    claim, description = retrieve_claim_description(client, "EP3721815", "B1")
    # print(claim, description)
    
    
            
        


        
