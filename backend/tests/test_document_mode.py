"""
DOCUMENT MODE Testing Guide
============================

This guide shows how to test the DOCUMENT MODE feature end-to-end.
"""

import requests
import json
from pathlib import Path

# Backend API base URL
BASE_URL = "http://localhost:8000/api"

def test_document_upload():
    """Test 1: Upload a document"""
    print("="*80)
    print("TEST 1: Upload Document")
    print("="*80)
    
    # Create a sample document for testing
    sample_content = """
    Clinical Trial Summary
    ======================
    
    Study: Phase III Trial of Drug X for Type 2 Diabetes
    
    Objective:
    To evaluate the efficacy and safety of Drug X in patients with Type 2 Diabetes.
    
    Methods:
    - Randomized, double-blind, placebo-controlled trial
    - 500 participants enrolled
    - 24-week treatment period
    
    Results:
    - HbA1c reduction: 1.2% (p<0.001)
    - Weight loss: 3.5 kg average
    - Adverse events: Mild gastrointestinal symptoms in 12% of patients
    
    Conclusion:
    Drug X demonstrated significant efficacy in reducing HbA1c with acceptable safety profile.
    """
    
    # Save sample document
    test_file_path = Path("test_clinical_trial.txt")
    with open(test_file_path, "w") as f:
        f.write(sample_content)
    
    # Upload the document
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_clinical_trial.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/upload/document", files=files)
        
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get("doc_id")
            print(f"✅ Upload successful!")
            print(f"   Document ID: {doc_id}")
            print(f"   Filename: {result.get('filename')}")
            return doc_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None
    finally:
        # Cleanup test file
        if test_file_path.exists():
            test_file_path.unlink()


def test_document_analysis(doc_id: str):
    """Test 2: Analyze the uploaded document"""
    print("\n" + "="*80)
    print("TEST 2: Analyze Document with DOCUMENT MODE")
    print("="*80)
    
    if not doc_id:
        print("❌ No document ID provided. Skipping analysis test.")
        return
    
    # Test chat request with document
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
            print(f"\nResponse:\n{'-'*80}")
            print(result.get("content", "No content"))
            print("-"*80)
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Analysis error: {e}")


def test_document_mode_without_upload():
    """Test 3: DOCUMENT MODE detection without uploaded file"""
    print("\n" + "="*80)
    print("TEST 3: DOCUMENT MODE Detection (No Upload)")
    print("="*80)
    
    test_prompts = [
        "Analyze this clinical trial document",
        "Summarize the key findings from this PDF",
        "Extract data from the uploaded file",
        "What does this research paper say?",
    ]
    
    for prompt in test_prompts:
        payload = {"message": prompt}
        
        try:
            response = requests.post(f"{BASE_URL}/chat/ask", json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"\n📝 Prompt: {prompt}")
                print(f"✅ Response:\n{result.get('content', '')[:200]}...")
            else:
                print(f"❌ Request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")


def print_usage_instructions():
    """Print usage instructions for manual testing"""
    print("\n" + "="*80)
    print("MANUAL TESTING INSTRUCTIONS")
    print("="*80)
    
    print("""
1. **Upload a Document via API**:
   ```bash
   curl -X POST http://localhost:8000/api/upload/document \\
     -F "file=@your_document.pdf"
   ```
   
   This returns a document ID like: `{"doc_id": "60d5ec9f..."}`

2. **Analyze Document via Chat**:
   ```bash
   curl -X POST http://localhost:8000/api/chats/ask \\
     -H "Content-Type: application/json" \\
     -d '{
       "message": "Analyze this clinical trial document",
       "metadata": {"document_id": "60d5ec9f..."}
     }'
   ```

3. **Test via Frontend**:
   - Upload document through file upload button
   - Ask: "Analyze this clinical trial document"
   - Frontend should include document_id in metadata

4. **DOCUMENT MODE Keywords** (auto-detection):
   - "analyze this document"
   - "summarize this PDF"
   - "extract data from this file"
   - "what does this paper say"
   - Any prompt with uploaded file

5. **Supported File Types**:
   - PDF (.pdf)
   - Word Documents (.docx)
   - Text Files (.txt)
   - Max size: 25MB

6. **Expected Behavior**:
   - ✅ DOCUMENT MODE detected automatically
   - ✅ InternalDocsAgent processes the file
   - ✅ Summary with metadata returned
   - ✅ No timeline events (not research mode)
   - ✅ Fast response (10-20 seconds)
    """)


def run_all_tests():
    """Run all DOCUMENT MODE tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "DOCUMENT MODE TEST SUITE" + " "*34 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Test 1: Upload document
    doc_id = test_document_upload()
    
    # Test 2: Analyze uploaded document
    if doc_id:
        test_document_analysis(doc_id)
    
    # Test 3: DOCUMENT MODE detection without upload
    test_document_mode_without_upload()
    
    # Print manual testing instructions
    print_usage_instructions()
    
    print("\n" + "="*80)
    print("✅ DOCUMENT MODE TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    print("""
    ⚠️  PREREQUISITES:
    1. Backend server must be running on http://localhost:8000
    2. MongoDB must be running
    3. Required Python packages: requests
    
    Run: pip install requests
    """)
    
    input("Press Enter to start tests...")
    run_all_tests()
