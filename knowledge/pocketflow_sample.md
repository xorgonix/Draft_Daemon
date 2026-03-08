from pocketflow import Node, Flow
from utils import call_llm

class UserInputNode(Node):
    def prep(self, shared):
        # Initialize messages if this is the first run
        if "messages" not in shared:
            shared["messages"] = []
            print("Welcome to the Travel Advisor Chat! Type 'exit' to end the conversation.")
        
        return None

    def exec(self, _):
        # Get user input
        user_input = input("\nYou: ")
        return user_input

    def post(self, shared, prep_res, exec_res):
        user_input = exec_res
        
        # Check if user wants to exit
        if user_input and user_input.lower() == 'exit':
            print("\nGoodbye! Safe travels!")
            return None  # End the conversation
        
        # Store user input in shared
        shared["user_input"] = user_input
        
        # Move to guardrail validation
        return "validate"

class GuardrailNode(Node):
    def prep(self, shared):
        # Get the user input from shared data
        user_input = shared.get("user_input", "")
        return user_input
    
    def exec(self, user_input):
        # Basic validation checks
        if not user_input or user_input.strip() == "":
            return False, "Your query is empty. Please provide a travel-related question."
        
        if len(user_input.strip()) < 3:
            return False, "Your query is too short. Please provide more details about your travel question."
        
        # LLM-based validation for travel topics
        prompt = f"""
Evaluate if the following user query is related to travel advice, destinations, planning, or other travel topics.
The chat should ONLY answer travel-related questions and reject any off-topic, harmful, or inappropriate queries.
User query: {user_input}
Return your evaluation in YAML format:
```yaml
valid: true/false
reason: [Explain why the query is valid or invalid]
```"""
        
        # Call LLM with the validation prompt
        messages = [{"role": "user", "content": prompt}]
        response = call_llm(messages)
        
        # Extract YAML content
        yaml_content = response.split("```yaml")[1].split("```")[0].strip() if "```yaml" in response else response
        
        import yaml
        result = yaml.safe_load(yaml_content)
        assert result is not None, "Error: Invalid YAML format"
        assert "valid" in result and "reason" in result, "Error: Invalid YAML format"
        is_valid = result.get("valid", False)
        reason = result.get("reason", "Missing reason in YAML response")
        
        return is_valid, reason
    
    def post(self, shared, prep_res, exec_res):
        is_valid, message = exec_res
        
        if not is_valid:
            # Display error message to user
            print(f"\nTravel Advisor: {message}")
            # Skip LLM call and go back to user input
            return "retry"
        
        # Valid input, add to message history
        shared["messages"].append({"role": "user", "content": shared["user_input"]})
        # Proceed to LLM processing
        return "process"

class LLMNode(Node):
    def prep(self, shared):
        # Add system message if not present
        if not any(msg.get("role") == "system" for msg in shared["messages"]):
            shared["messages"].insert(0, {
                "role": "system", 
                "content": "You are a helpful travel advisor that provides information about destinations, travel planning, accommodations, transportation, activities, and other travel-related topics. Only respond to travel-related queries and keep responses informative and friendly. Your response are concise in 100 words."
            })
        
        # Return all messages for the LLM
        return shared["messages"]

    def exec(self, messages):
        # Call LLM with the entire conversation history
        response = call_llm(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # Print the assistant's response
        print(f"\nTravel Advisor: {exec_res}")
        
        # Add assistant message to history
        shared["messages"].append({"role": "assistant", "content": exec_res})
        
        # Loop back to continue the conversation
        return "continue"

# Create the flow with nodes and connections
user_input_node = UserInputNode()
guardrail_node = GuardrailNode()
llm_node = LLMNode()

# Create flow connections
user_input_node - "validate" >> guardrail_node
guardrail_node - "retry" >> user_input_node  # Loop back if input is invalid
guardrail_node - "process" >> llm_node
llm_node - "continue" >> user_input_node     # Continue conversation

flow = Flow(start=user_input_node)

# Start the chat
if __name__ == "__main__":
    shared = {}
    flow.run(shared)
    
from openai import OpenAI
import os

def call_llm(messages):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    # Test the LLM call
    messages = [{"role": "user", "content": "In a few words, what's the meaning of life?"}]
    response = call_llm(messages)
    print(f"Prompt: {messages[0]['content']}")
    print(f"Response: {response}")None 
    
    
from pocketflow import Flow
from nodes import GetUserQuestionNode, RetrieveNode, AnswerNode, EmbedNode

def create_chat_flow():
    # Create the nodes
    question_node = GetUserQuestionNode()
    retrieve_node = RetrieveNode()
    answer_node = AnswerNode()
    embed_node = EmbedNode()
    
    # Connect the flow:
    # 1. Start with getting a question
    # 2. Retrieve relevant conversations
    # 3. Generate an answer
    # 4. Optionally embed old conversations
    # 5. Loop back to get the next question

    # Main flow path
    question_node - "retrieve" >> retrieve_node
    retrieve_node - "answer" >> answer_node
    
    # When we need to embed old conversations
    answer_node - "embed" >> embed_node
    
    # Loop back for next question
    answer_node - "question" >> question_node
    embed_node - "question" >> question_node
    
    # Create the flow starting with question node
    return Flow(start=question_node)

# Initialize the flow
chat_flow = create_chat_flow()     



from flow import chat_flow

def run_chat_memory_demo():
    """
    Run an interactive chat interface with memory retrieval.
    
    Features:
    1. Maintains a window of the 3 most recent conversation pairs
    2. Archives older conversations with embeddings
    3. Retrieves 1 relevant past conversation when needed
    4. Total context to LLM: 3 recent pairs + 1 retrieved pair
    """
    
    print("=" * 50)
    print("PocketFlow Chat with Memory")
    print("=" * 50)
    print("This chat keeps your 3 most recent conversations")
    print("and brings back relevant past conversations when helpful")
    print("Type 'exit' to end the conversation")
    print("=" * 50)
    
    # Run the chat flow
    chat_flow.run({})

if __name__ == "__main__":
    run_chat_memory_demo()
    
    
    
from pocketflow import Node
from utils.vector_index import create_index, add_vector, search_vectors
from utils.call_llm import call_llm
from utils.get_embedding import get_embedding

class GetUserQuestionNode(Node):
    def prep(self, shared):
        """Initialize messages if first run"""
        if "messages" not in shared:
            shared["messages"] = []
            print("Welcome to the interactive chat! Type 'exit' to end the conversation.")
        
        return None
    
    def exec(self, _):
        """Get user input interactively"""
        # Get interactive input from user
        user_input = input("\nYou: ")
            
        # Check if user wants to exit
        if user_input.lower() == 'exit':
            return None
            
        return user_input
    
    def post(self, shared, prep_res, exec_res):
        # If exec_res is None, the user wants to exit
        if exec_res is None:
            print("\nGoodbye!")
            return None  # End the conversation
            
        # Add user message to current messages
        shared["messages"].append({"role": "user", "content": exec_res})
        
        return "retrieve"

class AnswerNode(Node):
    def prep(self, shared):
        """Prepare context for the LLM"""
        if not shared.get("messages"):
            return None
            
        # 1. Get the last 3 conversation pairs (or fewer if not available)
        recent_messages = shared["messages"][-6:] if len(shared["messages"]) > 6 else shared["messages"]
        
        # 2. Add the retrieved relevant conversation if available
        context = []
        if shared.get("retrieved_conversation"):
            # Add a system message to indicate this is a relevant past conversation
            context.append({
                "role": "system", 
                "content": "The following is a relevant past conversation that may help with the current query:"
            })
            context.extend(shared["retrieved_conversation"])
            context.append({
                "role": "system", 
                "content": "Now continue the current conversation:"
            })
        
        # 3. Add the recent messages
        context.extend(recent_messages)
        
        return context
    
    def exec(self, messages):
        """Generate a response using the LLM"""
        if messages is None:
            return None
        
        # Call LLM with the context
        response = call_llm(messages)
        return response
    
    def post(self, shared, prep_res, exec_res):
        """Process the LLM response"""
        if prep_res is None or exec_res is None:
            return None  # End the conversation
        
        # Print the assistant's response
        print(f"\nAssistant: {exec_res}")
        
        # Add assistant message to history
        shared["messages"].append({"role": "assistant", "content": exec_res})
        
        # If we have more than 6 messages (3 conversation pairs), archive the oldest pair
        if len(shared["messages"]) > 6:
            return "embed"
        
        # We only end if the user explicitly typed 'exit'
        # Even if last_question is set, we continue in interactive mode
        return "question"

class EmbedNode(Node):
    def prep(self, shared):
        """Extract the oldest conversation pair for embedding"""
        if len(shared["messages"]) <= 6:
            return None
            
        # Extract the oldest user-assistant pair
        oldest_pair = shared["messages"][:2]
        # Remove them from current messages
        shared["messages"] = shared["messages"][2:]
        
        return oldest_pair
    
    def exec(self, conversation):
        """Embed a conversation"""
        if not conversation:
            return None
            
        # Combine user and assistant messages into a single text for embedding
        user_msg = next((msg for msg in conversation if msg["role"] == "user"), {"content": ""})
        assistant_msg = next((msg for msg in conversation if msg["role"] == "assistant"), {"content": ""})
        combined = f"User: {user_msg['content']} Assistant: {assistant_msg['content']}"
        
        # Generate embedding
        embedding = get_embedding(combined)
        
        return {
            "conversation": conversation,
            "embedding": embedding
        }
    
    def post(self, shared, prep_res, exec_res):
        """Store the embedding and add to index"""
        if not exec_res:
            # If there's nothing to embed, just continue with the next question
            return "question"
            
        # Initialize vector index if not exist
        if "vector_index" not in shared:
            shared["vector_index"] = create_index()
            shared["vector_items"] = []  # Track items separately
            
        # Add the embedding to the index and store the conversation
        position = add_vector(shared["vector_index"], exec_res["embedding"])
        shared["vector_items"].append(exec_res["conversation"])
        
        print(f"✅ Added conversation to index at position {position}")
        print(f"✅ Index now contains {len(shared['vector_items'])} conversations")
        
        # Continue with the next question
        return "question"

class RetrieveNode(Node):
    def prep(self, shared):
        """Get the current query for retrieval"""
        if not shared.get("messages"):
            return None
            
        # Get the latest user message for searching
        latest_user_msg = next((msg for msg in reversed(shared["messages"]) 
                                if msg["role"] == "user"), {"content": ""})
        
        # Check if we have a vector index with items
        if ("vector_index" not in shared or 
            "vector_items" not in shared or 
            len(shared["vector_items"]) == 0):
            return None
            
        return {
            "query": latest_user_msg["content"],
            "vector_index": shared["vector_index"],
            "vector_items": shared["vector_items"]
        }
    
    def exec(self, inputs):
        """Find the most relevant past conversation"""
        if not inputs:
            return None
            
        query = inputs["query"]
        vector_index = inputs["vector_index"]
        vector_items = inputs["vector_items"]
        
        print(f"🔍 Finding relevant conversation for: {query[:30]}...")
        
        # Create embedding for the query
        query_embedding = get_embedding(query)
        
        # Search for the most similar conversation
        indices, distances = search_vectors(vector_index, query_embedding, k=1)
        
        if not indices:
            return None
            
        # Get the corresponding conversation
        conversation = vector_items[indices[0]]
        
        return {
            "conversation": conversation,
            "distance": distances[0]
        }
    
    def post(self, shared, prep_res, exec_res):
        """Store the retrieved conversation"""
        if exec_res is not None:
            shared["retrieved_conversation"] = exec_res["conversation"]
            print(f"📄 Retrieved conversation (distance: {exec_res['distance']:.4f})")
        else:
            shared["retrieved_conversation"] = None
        
        return "answer"
    

utils directoroyh:


import os
from openai import OpenAI

def call_llm(messages):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    # Test the LLM call
    messages = [{"role": "user", "content": "In a few words, what's the meaning of life?"}]
    response = call_llm(messages)
    print(f"Prompt: {messages[0]['content']}")
    print(f"Response: {response}") 

import os
import numpy as np
from openai import OpenAI

def get_embedding(text):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY"))
    
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    
    # Extract the embedding vector from the response
    embedding = response.data[0].embedding
    
    # Convert to numpy array for consistency with other embedding functions
    return np.array(embedding, dtype=np.float32)


if __name__ == "__main__":
    # Test the embedding function
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "Python is a popular programming language for data science."
    
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    
    print(f"Embedding 1 shape: {emb1.shape}")
    print(f"Embedding 2 shape: {emb2.shape}")
    
    # Calculate similarity (dot product)
    similarity = np.dot(emb1, emb2)
    print(f"Similarity between texts: {similarity:.4f}") 
    import numpy as np
    import faiss
    
    def create_index(dimension=1536):
        return faiss.IndexFlatL2(dimension)
    
    def add_vector(index, vector):
        # Make sure the vector is a numpy array with the right shape for FAISS
        vector = np.array(vector).reshape(1, -1).astype(np.float32)
        
        # Add the vector to the index
        index.add(vector)
        
        # Return the position (index.ntotal is the total number of vectors in the index)
        return index.ntotal - 1
    
    def search_vectors(index, query_vector, k=1):
        """Search for the k most similar vectors to the query vector
        
        Args:
            index: The FAISS index
            query_vector: The query vector (numpy array or list)
            k: Number of results to return (default: 1)
            
        Returns:
            tuple: (indices, distances) where:
                - indices is a list of positions in the index
                - distances is a list of the corresponding distances
        """
        # Make sure we don't try to retrieve more vectors than exist in the index
        k = min(k, index.ntotal)
        if k == 0:
            return [], []
            
        # Make sure the query is a numpy array with the right shape for FAISS
        query_vector = np.array(query_vector).reshape(1, -1).astype(np.float32)
        
        # Search the index
        distances, indices = index.search(query_vector, k)
        
        return indices[0].tolist(), distances[0].tolist()
    
    # Example usage
    if __name__ == "__main__":
        # Create a new index
        index = create_index(dimension=3)
        
        # Add some random vectors and track them separately
        items = []
        for i in range(5):
            vector = np.random.random(3)
            position = add_vector(index, vector)
            items.append(f"Item {i}")
            print(f"Added vector at position {position}")
            
        print(f"Index contains {index.ntotal} vectors")
        
        # Search for a similar vector
        query = np.random.random(3)
        indices, distances = search_vectors(index, query, k=2)
        
        print("Query:", query)
        
        print("Found indices:", indices)
        print("Distances:", distances)
        print("Retrieved items:", [items[idx] for idx in indices])
