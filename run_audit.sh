#!/bin/bash
echo "=== Baseline Test Suite ==="
python -m pytest tests/test_iterative_methods.py
echo ""
echo "=== Benchmarks ==="
python experiments/run_benchmarks.py
echo ""
echo "=== Symbolic Order Check ==="
python experiments/symbolic_order.py
