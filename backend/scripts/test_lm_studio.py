"""
Test script to verify LM Studio is running and responding
"""
import asyncio
import httpx
import json

LM_STUDIO_URL = "http://localhost:1234/v1"

async def test_lm_studio():
    """Test LM Studio connection and basic functionality"""
    print("=" * 60)
    print("LM STUDIO CONNECTION TEST")
    print("=" * 60)
    
    # Test 1: Check if LM Studio is running
    print("\n1. Testing connection to LM Studio...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LM_STUDIO_URL}/models")
            if response.status_code == 200:
                print("   ✅ LM Studio is running!")
                models = response.json()
                print(f"   Available models: {json.dumps(models, indent=2)}")
            else:
                print(f"   ⚠️ LM Studio responded with status {response.status_code}")
                print(f"   Response: {response.text}")
    except httpx.ConnectError:
        print("   ❌ FAILED: Cannot connect to LM Studio on http://localhost:1234")
        print("   Please ensure:")
        print("      - LM Studio is installed and running")
        print("      - A model is loaded in LM Studio")
        print("      - The server is started on port 1234")
        return False
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        return False
    
    # Test 2: Test chat completion with multiple model name variations
    print("\n2. Testing chat completion...")
    
    # Try different model name variations
    model_names = [
        "mistral-7b-instruct-v0.3-q6_k",
        "TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
        "lmstudio-community/mistral-7b-instruct-v0.3-q6_k",
        "mistral-7b-instruct-v0.3.Q6_K.gguf"
    ]
    
    for model_name in model_names:
        print(f"\n   Testing model name: '{model_name}'")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "Say 'Working' and nothing else."}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20
                }
                
                response = await client.post(
                    f"{LM_STUDIO_URL}/chat/completions",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"   ✅ SUCCESS with model name: '{model_name}'")
                    print(f"   Response: {content}")
                    print(f"\n   🎯 USE THIS MODEL NAME IN .env: {model_name}")
                    return True
                else:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    if response.status_code == 400:
                        print(f"   Error: {response.text[:200]}")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # If none worked
    print("\n   ❌ No model name worked!")
    print("   Please check:")
    print("      1. Open LM Studio")
    print("      2. Go to 'Local Server' tab")  
    print("      3. Check the EXACT model name shown")
    print("      4. Copy that name to LMSTUDIO_MODEL_NAME in .env")
    return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_lm_studio())
    exit(0 if result else 1)
