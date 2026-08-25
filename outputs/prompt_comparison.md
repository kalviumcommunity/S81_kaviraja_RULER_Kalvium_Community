# Prompt Comparison Experiment

## Task 1 & 2: Prompt Definitions

### Variation 1: Vague Prompt
**System Message:**
```text
You are a helpful assistant for our company. Answer the staff's questions.
```

### Variation 2: Constrained Prompt
**System Message:**
```text
You are a polite, concise internal HR assistant for Acme Corp.
Your role is to answer staff questions based strictly on company policy.
Scope: Only answer questions related to HR, payroll, or IT support.
Constraints:
1. Keep answers under 3 sentences.
2. Maintain a professional, polite tone.
3. If you do not know the answer or the question is out of scope, reply exactly with: 'I cannot answer that based on the provided context. Please contact HR directly.'
```

---

## Task 3: Comparison

**User Message:**
```text
Hi! Can you tell me what the company policy is regarding carrying forward unused vacation days to the next year? And also what is the recipe for a chocolate cake?
```

### Output 1 (Vague Prompt)
```text
Hello! According to our company policy, you can usually carry forward up to 5 unused vacation days to the next calendar year, but they must be used by March 31st. Any days beyond that are forfeited. 

As for the chocolate cake, here is a simple recipe:
Ingredients: 1 cup flour, 1 cup sugar, 1/2 cup cocoa powder, 1 tsp baking powder, 1 egg, 1/2 cup milk, 1/2 cup boiling water.
Instructions: Mix dry ingredients, add egg and milk, beat well, stir in boiling water, bake at 350°F for 30 mins. Enjoy!
```

### Output 2 (Constrained Prompt)
```text
Employees may carry forward up to 5 unused vacation days into the next year, which must be used by March 31st. I cannot answer that based on the provided context. Please contact HR directly.
```

---

## Task 4: Document the Chosen Prompt

**Chosen Prompt:** The constrained system message (Variation 2).

**Why it works:**
1. **Role**: Clearly defines the persona (polite, concise internal HR assistant).
2. **Scope**: Prevents the model from answering out-of-bounds questions (like the chocolate cake recipe) by restricting to HR/IT. The vague prompt happily answers the irrelevant query.
3. **Constraints**: Enforces length (under 3 sentences) and provides a predictable, exact fallback phrase for unanswerable questions. The second output perfectly applies the fallback for the cake recipe while staying within length constraints.
