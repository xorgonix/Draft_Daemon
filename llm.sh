 1 #!/bin/bash                                                            │
  │     2 # Test script for Ollama LLM                                           │
  │     3 # Run this to verify Ollama is responding correctly                    │
  │     4                                                                        │
  │     5 echo "============================================================"    │
  │     6 echo "Testing Ollama LLM Connection"                                   │
  │     7 echo "============================================================"    │
  │     8 echo ""                                                                │
  │     9                                                                        │
  │    10 echo "Sending request to Ollama..."                                    │
  │    11 echo "Model: gemma3-12b-32k:latest"                                    │
  │    12 echo ""                                                                │
  │    13                                                                        │
  │    14 curl -X POST http://localhost:11434/api/chat \                         │
  │    15   -H "Content-Type: application/json" \                                │
  │    16   -d '{                                                                │
  │    17     "model": "gemma3-12b-32k:latest",                                  │
  │    18     "messages": [                                                      │
  │    19       {"role": "user", "content": "Say hello in 5 words or less"}      │
  │    20     ],                                                                 │
  │    21     "stream": false                                                    │
  │    22   }'                                                                   │
  │    23                                                                        │
  │    24 echo ""                                                                │
  │    25 echo ""                                                                │
  │    26 echo "============================================================"    │
  │    27 echo "Test complete"                                                   │
  │    28 echo "============================================================"
