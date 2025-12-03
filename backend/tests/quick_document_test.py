"""
Quick DOCUMENT MODE Test - No User Input Required
Tests document upload and analysis workflow automatically
"""

import requests
import json
from io import BytesIO

BASE_URL = "http://localhost:8000/api"

def test_document_workflow():
    """Test complete document upload and analysis workflow"""
    
    print("\n" + "="*80)
    print("QUICK DOCUMENT MODE TEST")
    print("="*80)
    
    # Step 1: Upload a sample document
    print("\n[1/3] Uploading sample document...")
    
    sample_content = """
    Clinical Trial Summary: Drug X for Type 2 Diabetes
    
    Phase: Phase III
    Participants: 500 patients
    Duration: 12 months
    
    Key Findings:
    - Primary endpoint met: 85% reduction in HbA1c levels
    - Secondary endpoints: Improved insulin sensitivity, weight loss
    - Adverse events: Mild nausea (12%), headache (8%)
    - No serious adverse events reported
    
    Conclusion: Drug X demonstrates significant efficacy in treating Type 2 Diabetes
    with an acceptable safety profile.
    """
    
    try:
        files = {'file': ('clinical_trial_sample.txt', BytesIO(sample_content.encode()))}
        response = requests.post(f"{BASE_URL}/upload/document", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            doc_id = upload_result.get('document_id')
            print(f"✅ Upload successful!")
            print(f"   Document ID: {doc_id}")
            print(f"   Filename: {upload_result.get('filename')}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Upload error: {e}")
        print("   Is the backend server running on http://localhost:8000?")
        return
    
    # Step 2: Analyze document with DOCUMENT MODE
    print("\n[2/3] Analyzing document with DOCUMENT MODE...")
    
    payload = {
        "message": "Analyze this clinical trial document and summarize the key findings",
        "metadata": {
            "document_id": doc_id
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat/ask", json=payload)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Analysis successful!")
            print(f"\n{'='*80}")
            print("RESPONSE:")
            print("="*80)
            print(result.get("content", "No content"))
            print("="*80)
            
            # Verify DOCUMENT MODE was used
            if "Document Analysis" in result.get("content", ""):
                print("\n✅ DOCUMENT MODE confirmed (formatted response detected)")
            else:
                print("\n⚠️  Response format unexpected - check Mode Engine")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return
    
    # Step 3: Test keyword detection (without document_id)
    print("\n[3/3] Testing DOCUMENT MODE keyword detection...")
    
    test_prompts = [
        "Analyze this document",
        "Summarize the PDF"
    ]
    
    for prompt in test_prompts:
        payload = {"message": prompt}
        
        try:
            response = requests.post(f"{BASE_URL}/chat/ask", json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                content = result.get("content", "")
                
                # Check if it asks for document upload
                if "upload" in content.lower() or "document" in content.lower():
                    print(f"✅ '{prompt}' - Properly handled (asks for upload)")
                else:
                    print(f"⚠️  '{prompt}' - Unexpected response")
            else:
                print(f"❌ '{prompt}' - Request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ '{prompt}' - Error: {e}")
    
    print("\n" + "="*80)
    print("✅ QUICK TEST COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Test with real PDF/DOCX files via upload endpoint")
    print("2. Integrate file upload UI in frontend")
    print("3. Test streaming endpoint with document analysis")
    print("="*80)


if __name__ == "__main__":
    test_document_workflow()
