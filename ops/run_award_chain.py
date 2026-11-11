"""Use the frozen real chain with the separate award quota and provenance."""
import run_r3_chain
from award_lux_budget import AwardBudget

if __name__ == '__main__':
    run_r3_chain.R3Budget = AwardBudget
    run_r3_chain.main()
