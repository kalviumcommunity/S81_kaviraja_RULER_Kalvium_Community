# Retrieval Tuning Report

## Queries
- What is the ideal characteristic of artificial intelligence? (Expected: ability to rationalize)
- What is machine learning? (Expected: automatically learn from and adapt)

## Results
{
  "Setting_A": {
    "k_results": {
      "k=1": {
        "hit_rate": 1.0,
        "avg_similarity": 0.6894111335277557
      },
      "k=2": {
        "hit_rate": 1.0,
        "avg_similarity": 0.6894111335277557
      }
    }
  },
  "Setting_B": {
    "k_results": {
      "k=1": {
        "hit_rate": 1.0,
        "avg_similarity": 0.6615740358829498
      },
      "k=2": {
        "hit_rate": 1.0,
        "avg_similarity": 0.6615740358829498
      }
    }
  }
}

## Conclusion
The best configuration is Setting_A with k=1. Setting A (30 tokens) vs Setting B (60 tokens) showed that the chosen setting maximized hit rate and semantic similarity for the given queries. A top-k of k=1 provided the best trade-off between getting the relevant chunk and maintaining precision.