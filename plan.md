1. **Fix Abstract in `paper/main.tex`:**
   - Correct the error recurrence term $O(e_n^4)$ coefficient from `(14A_2^3-8A_2A_3)` to `A_2(5A_2^2-A_3)`.

2. **Fix Section 3 (Convergence analysis) in `paper/main.tex`:**
   - Correct the error recurrence in eq. (3) from `(5A_2^3-A_2A_3)` to `A_2(5A_2^2-A_3)`.
   - Update the degeneracy check from `5A_2^3-A_2A_3 \neq 0` to `A_2(5A_2^2-A_3) \neq 0`.

3. **Update Evidence Ledger `research/evidence_ledger.md`:**
   - Update the E2 claim text to reflect the correct error coefficient `A2(5A2^2-A3)`.

4. **Rebuild PDF:**
   - Compile the latex file to update `paper/main.pdf`.

5. **Pre-commit Steps:**
   - Execute the `pre_commit_instructions` tool to make sure proper testing, verifications, reviews, and reflections are completed successfully.

6. **Submit PR:**
   - Use `submit` to commit changes and open a pull request.
