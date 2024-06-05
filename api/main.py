from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lib.open_ai import generate_fermi_problem, generate_estimate

app = FastAPI()


@app.get("/")
def generate_problem():
    return generate_fermi_problem()


class FermiProblemEstimateRequest(BaseModel):
    fermi_problem: str


@app.post("/estimate")
def make_estimations(req: FermiProblemEstimateRequest):
    """Get the specified number of estimations for the Fermi Problem then average the results and round to the nearest whole number within the order of magnitude.
    E.g. 1234 -> 1000

    Args:
    fermi_problem (str): The Fermi Problem to be solved

    Returns:
    int: The estimated final value of the Fermi Problem
    """
    NUM_ESTIMATES = 3

    estimates = []
    for _ in range(NUM_ESTIMATES):
        try:
            estimates.append(generate_estimate(req.fermi_problem))
        except Exception as e:
            try:
                estimates.append(generate_estimate(req.fermi_problem))
            except Exception as e:
                print(f"Error: {e} - skipping this estimate")

    average_estimate = sum(estimates) / len(estimates)
    rounded_estimate = round(
        average_estimate, -len(str(int(average_estimate))) + 1
    )  # round to the nearest whole number within the order of magnitude

    return rounded_estimate
