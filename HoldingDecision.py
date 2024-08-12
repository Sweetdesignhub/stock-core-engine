
from fastapi import FastAPI, HTTPException
import requests
import pandas as pd
from pydantic import BaseModel

app = FastAPI()

class HoldingsRequest(BaseModel):
    userId: str
    marginProfit:float
    marginLoss:float


class HoldingsResponse(BaseModel):
    holdings: list

def make_decision(response: dict, margin_profit: float, margin_loss: float) -> dict:

    df = pd.DataFrame(data=response['holdings'])
    df = df[['symbol', 'quantity', 'costPrice', 'pl']]
    df.columns = ['Symbol', 'Quantity', 'Cost price', 'P&L']

    df['Margin_Profit'] = (margin_profit / 100) * df['Cost price']
    df['Margin_Loss'] = (margin_loss / 100) * df['Cost price']

    df['Decision'] = df.apply(
        lambda row: 'Sell' if row['P&L'] >= row['Margin_Profit'] 
        else 'Sell' if row['P&L'] <= -row['Margin_Loss'] 
        else 'Hold', 
        axis=1
    )

    return df.to_dict(orient='index')

@app.post("/autoTradingActivated")
def fetch_all_fyers_user_details(request: HoldingsRequest):
    user_id = request.userId
    margin_profit = request.marginProfit
    margin_loss = request.marginLoss
    url = f'https://api.stockgenius.ai/api/v1/fyers/holdingsByUserId/{user_id}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        data = response.json()
        decision = make_decision(data,margin_profit, margin_loss)
        return decision
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Fyers user details: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
