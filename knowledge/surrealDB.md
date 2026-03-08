Defining the Scope

I have defined the scope: creating a quick-reference guide for an LLM using SurrealDB 3.0.

Reviewing Key Features

I've reviewed SurrealDB 3.0's features, noting computed fields, AI agent capabilities, and indexing improvements.

Focusing on FTS

I've outlined FTS elements: defining analyzers, indexes, querying with operators, and functions like search::highlight().

Gemini said
Here is a distilled, LLM-optimized guide for SurrealDB 3.0. It is structured to provide an AI with exactly what it needs to understand the syntax, updated features, and multi-model paradigms without the marketing fluff.

SurrealDB 3.0: LLM Developer Instruction Guide
1. Core 3.0 Changes & Deprecations
DO NOT USE future: Futures are deprecated. Use COMPUTED fields instead. Computed fields are evaluated at query time.

Syntax: DEFINE FIELD valid ON license COMPUTED time::now() - since < 2y;

Bidirectional Record References: Unidirectional links can now be bidirectional using the REFERENCE clause and traversed using <~.

Schema: DEFINE FIELD owner ON license TYPE record<person> REFERENCE;

Query: SELECT ->owner, <~license FROM person;

Client-Side Transactions: Application logic can now manage transaction states (Begin -> Operations -> Commit/Cancel) via SDKs (Rust, Go, JS/TS) rather than forcing all logic into single SurrealQL queries.

2. Document & CRUD Operations
SurrealDB operates schemaless or schemafull. Records are identified by table_name:id.

Create: CREATE person:one SET name = "John", age = 30;

Insert (Multiple): INSERT INTO person [{name: "John"}, {name: "Jane"}];

Read: SELECT * FROM person WHERE name = "Jane" LIMIT 10;

Update: UPDATE person SET last_name = "Doe" WHERE name = "Jane";

Delete: DELETE person WHERE name = "Jane";

3. Graph Database Modeling (Nodes & Edges)
Use graph relations when edges need properties/metadata. For simple pointers without metadata, use standard Record Links (TYPE record<table_name>).

Define Relation Table: Enforces strict node connections.

DEFINE TABLE likes TYPE RELATION IN person OUT blog_post | book;

Relate Records: Creates an edge (in -> id -> out) with optional properties.

RELATE person:1->likes->book:1 SET rating = 5, created_at = time::now();

Graph Traversal: Use arrow syntax (->, <-, <->).

Forward: SELECT ->likes->book FROM person:1;

Reverse: SELECT <-likes<-person FROM book:1;

Bidirectional (Equals): SELECT <->friends_with<->person FROM person;

Unique Edge Constraints: Prevent duplicate relations.

DEFINE FIELD key ON TABLE friends_with VALUE <string>array::sort([in, out]);

DEFINE INDEX only_one ON TABLE friends_with FIELDS key UNIQUE;

4. Vector Database & AI Integration
Store and query high-dimensional vector embeddings for semantic search.

Define Index (HNSW):

DEFINE INDEX hnsw_idx ON table FIELDS embedding HNSW DIMENSION 1536 DIST COSINE;

Vector Querying:

Index lookup: SELECT * FROM table WHERE embedding <|5|> $query_vector; (Returns top 5).

Brute force: SELECT * FROM table WHERE embedding <|5, EUCLIDEAN|> $query_vector;

KNN Function: Retrieve distance score without recomputation.

SELECT *, vector::distance::knn() AS dist FROM table WHERE embedding <|2|> $query_vector;

Native File Storage (New in 3.0):

Setup: DEFINE BUCKET my_bucket BACKEND "memory";

Operations: f"my_bucket:/file.txt".put("content"); or .get();

Lossy strings: type::string_lossy(<bytes>f"my_bucket:/file.txt".get())

5. Full-Text Search (FTS)
Index text using tokenizers and filters for relevance-based matching.

Define Analyzer:

DEFINE ANALYZER my_analyzer TOKENIZERS blank, punct FILTERS lowercase, snowball(english);

Define Index (BM25): Must be on a single field.

DEFINE INDEX text_idx ON TABLE article FIELDS body FULLTEXT ANALYZER my_analyzer BM25 HIGHLIGHTS;

Match Operators:

Basic Match: SELECT * FROM article WHERE body @@ "machine learning";

Boolean Match: WHERE body @AND@ "machine learning" or WHERE body @OR@ "fast slow"

Scoring & Highlighting: Match tags (e.g., @0@) correspond to function arguments.

SELECT search::score(0) AS score, search::highlight("<b>", "</b>", 0) FROM article WHERE body @0@ "search term";

6. APIs & WebAssembly Extensions
Custom API Endpoints: Define HTTP endpoints directly in the database.

DEFINE API OVERWRITE "/get_latest" FOR get MIDDLEWARE api::timeout(50ms) THEN { RETURN { body: SELECT * FROM comment:[time::now()-10m].. } };

Surrealism: Execute custom WebAssembly (Rust) logic directly within the DB for AI pipelines, custom auth, or complex validation.
