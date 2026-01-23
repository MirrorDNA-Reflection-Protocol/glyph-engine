"""
⟡ Beacon API — FastAPI server for verification endpoints

Run with: uvicorn glyph_engine.api:app --port 8090

Endpoints:
- GET /verify/{beacon_id} — Verify a beacon
- GET /proof/{beacon_id}  — Get inclusion proof
- GET /registry          — Get full registry
- GET /health            — Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import yaml

from glyph_engine.proof import BeaconProof, verify_beacon, generate_verification_badge


app = FastAPI(
    title="⟡ Beacon Verify API",
    description="Cryptographic verification for AI artifact provenance",
    version="1.0.0",
)

# Enable CORS for web demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Initialize proof system
REGISTRY_PATH = Path(__file__).parent.parent / "beacon_registry" / "BEACON_REGISTRY.yaml"
prover = BeaconProof(REGISTRY_PATH)


@app.get("/")
async def root():
    """Redirect to verification page."""
    return HTMLResponse(content="""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/docs">
            <style>body{background:#0a0a0f;color:#e0e0e8;font-family:system-ui;display:flex;justify-content:center;align-items:center;height:100vh;}</style>
        </head>
        <body>
            <div style="text-align:center;">
                <div style="font-size:4rem;">⟡</div>
                <h1>Beacon Verify API</h1>
                <p>Redirecting to docs...</p>
            </div>
        </body>
    </html>
    """)


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "merkle_root": prover.get_root_hash()[:16] if prover.get_root_hash() else None,
        "beacon_count": len(prover._beacons),
    }


@app.get("/verify/{beacon_id}")
async def verify_endpoint(beacon_id: str):
    """
    Verify a beacon exists in the registry.
    
    Returns verification result with cryptographic proof.
    """
    result = verify_beacon(beacon_id.upper(), REGISTRY_PATH)
    
    if not result["verified"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Beacon not found"))
    
    return result


@app.get("/proof/{beacon_id}")
async def proof_endpoint(beacon_id: str):
    """
    Get Merkle inclusion proof for a beacon.
    
    This proof can be verified offline.
    """
    proof = prover.generate_inclusion_proof(beacon_id.upper())
    
    if proof is None:
        raise HTTPException(status_code=404, detail=f"Beacon {beacon_id} not found")
    
    return proof.to_dict()


@app.get("/zkp/{beacon_id}")
async def zkp_endpoint(beacon_id: str):
    """
    Generate zero-knowledge commitment.
    
    Proves beacon membership without revealing which beacon.
    """
    commitment = prover.generate_zkp_commitment(beacon_id.upper())
    
    if commitment is None:
        raise HTTPException(status_code=404, detail=f"Beacon {beacon_id} not found")
    
    return commitment


@app.get("/registry")
async def registry_endpoint():
    """
    Get full registry (public data only).
    """
    if not REGISTRY_PATH.exists():
        raise HTTPException(status_code=500, detail="Registry not found")
    
    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f)
    
    return {
        "beacons": data.get("beacons", []),
        "merkle_root": prover.get_root_hash(),
        "integrity": prover.verify_registry_integrity(),
    }


@app.get("/badge/{beacon_id}")
async def badge_endpoint(beacon_id: str):
    """
    Get embeddable badge markdown.
    """
    result = verify_beacon(beacon_id.upper(), REGISTRY_PATH)
    
    return {
        "beacon_id": beacon_id.upper(),
        "verified": result["verified"],
        "markdown": generate_verification_badge(beacon_id.upper()),
    }


# Serve static web page
@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Serve the verification demo page."""
    html_path = Path(__file__).parent.parent / "web" / "index.html"
    if html_path.exists():
        with open(html_path) as f:
            return f.read()
    else:
        return "<h1>Demo page not found</h1>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
