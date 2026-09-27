"""
app.py -- Person B | THE DEMO SURFACE

EcoLLM -- Sovereign On-Premise Agentic AI Workbench

Stdlib only.
No Flask.
No pip.
No CDN.
No external assets.

Runs entirely on localhost:

    python app.py

Then open:

    http://localhost:8080
"""

import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

import agent
from router import route


PORT = 8080
UPLOADS = "uploads"
OUTPUT = "output"


PAGE = r"""<!doctype html>
<html>
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>EcoLLM — Sovereign AI Workbench</title>

<style>

/* =========================================================
   DESIGN SYSTEM
   ========================================================= */

:root {
    --bg: #080c11;
    --surface: #0e141b;
    --surface-2: #121a23;
    --surface-3: #17212c;

    --border: #26323e;
    --border-light: #334252;

    --text: #e8edf3;
    --muted: #8996a5;
    --muted-2: #5e6b79;

    --blue: #55b9ff;
    --blue-dark: #163b54;

    --green: #45d47b;
    --green-dark: #173b28;

    --yellow: #e6b94e;
    --yellow-dark: #3c321b;

    --red: #ef6a6a;
    --red-dark: #3d2020;

    --radius: 10px;
}


/* =========================================================
   BASE
   ========================================================= */

* {
    box-sizing: border-box;
}

html {
    background: var(--bg);
}

body {
    margin: 0;
    min-height: 100vh;

    background:
        radial-gradient(
            circle at 50% -15%,
            rgba(63, 135, 185, 0.10),
            transparent 38%
        ),
        var(--bg);

    color: var(--text);

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    font-size: 14px;
    line-height: 1.5;
}

button,
textarea,
input {
    font: inherit;
}


/* =========================================================
   HEADER
   ========================================================= */

.header {
    height: 68px;

    padding: 0 34px;

    display: flex;
    align-items: center;
    justify-content: space-between;

    border-bottom: 1px solid var(--border);

    background: rgba(8, 12, 17, 0.96);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.logo {
    width: 35px;
    height: 35px;

    display: grid;
    place-items: center;

    border: 1px solid #315a75;
    border-radius: 8px;

    background: #0d1923;

    color: var(--blue);

    font-weight: 800;
    font-size: 14px;
}

.brand-name {
    font-size: 17px;
    font-weight: 750;
    letter-spacing: -0.02em;
}

.brand-subtitle {
    margin-top: 1px;

    color: var(--muted);

    font-size: 10px;
    letter-spacing: 0.03em;
}

.airgap {
    display: flex;
    align-items: center;
    gap: 8px;

    padding: 7px 12px;

    border: 1px solid #285c3c;
    border-radius: 999px;

    background: rgba(52, 132, 78, 0.08);

    color: #78e59f;

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.08em;
}

.airgap-dot {
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--green);

    box-shadow:
        0 0 8px rgba(69, 212, 123, 0.65);
}


/* =========================================================
   MAIN
   ========================================================= */

main {
    width: min(1080px, calc(100% - 40px));

    margin: 0 auto;

    padding: 38px 0 70px;
}

.eyebrow {
    color: var(--blue);

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.14em;
    text-transform: uppercase;
}

h1 {
    margin: 7px 0 7px;

    font-size: 30px;
    line-height: 1.15;

    letter-spacing: -0.04em;
}

.subtitle {
    max-width: 720px;

    margin: 0 0 27px;

    color: var(--muted);

    font-size: 13px;
}


/* =========================================================
   WORKSPACE
   ========================================================= */

.workspace {
    padding: 20px;

    border: 1px solid var(--border);
    border-radius: var(--radius);

    background:
        linear-gradient(
            145deg,
            rgba(18, 27, 37, 0.96),
            rgba(12, 17, 24, 0.98)
        );
}

.section-label {
    margin-bottom: 9px;

    color: var(--muted);

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.12em;
    text-transform: uppercase;
}


/* =========================================================
   TASK MODES
   ========================================================= */

.modes {
    display: flex;
    gap: 7px;

    flex-wrap: wrap;

    margin-bottom: 15px;
}

.mode {
    position: relative;

    padding: 7px 13px;

    border: 1px solid var(--border-light);
    border-radius: 7px;

    background: #0b1118;

    color: var(--muted);

    font-size: 11px;
    font-weight: 650;

    cursor: pointer;

    transition:
        background 0.15s,
        border-color 0.15s,
        color 0.15s;
}

.mode:hover {
    border-color: #466078;
    color: var(--text);
}

.mode.active {
    border-color: #397da7;

    background: #102535;

    color: #9bd8ff;
}

.mode-name {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.mode-dot {
    width: 5px;
    height: 5px;

    border-radius: 50%;

    background: currentColor;
}

.mode-description {
    margin: 0 0 14px;

    color: var(--muted-2);

    font-size: 11px;
}


/* =========================================================
   PROMPT
   ========================================================= */

textarea {
    width: 100%;
    min-height: 116px;

    padding: 15px 16px;

    resize: vertical;

    outline: none;

    border: 1px solid var(--border-light);
    border-radius: 8px;

    background: #090e14;

    color: var(--text);

    font-size: 14px;

    transition:
        border-color 0.15s,
        box-shadow 0.15s;
}

textarea::placeholder {
    color: #596575;
}

textarea:focus {
    border-color: #397da7;

    box-shadow:
        0 0 0 3px rgba(85, 185, 255, 0.06);
}


/* =========================================================
   CONTROLS
   ========================================================= */

.controls {
    display: flex;
    align-items: stretch;

    gap: 12px;

    margin-top: 12px;
}

.upload {
    flex: 1;

    min-height: 48px;

    display: flex;
    align-items: center;

    padding: 0 13px;

    border: 1px dashed #3a4a5a;
    border-radius: 8px;

    background: #0a1017;

    cursor: pointer;

    transition:
        border-color 0.15s,
        background 0.15s;
}

.upload:hover {
    border-color: #4d718c;
    background: #0d141c;
}

.upload.has-file {
    border-style: solid;

    border-color: #315f7d;

    background: #0c1821;
}

.upload-icon {
    width: 34px;

    color: var(--blue);

    font-size: 19px;
    text-align: center;
}

.upload-copy {
    min-width: 0;
}

.upload-title {
    overflow: hidden;

    color: var(--text);

    font-size: 12px;
    font-weight: 650;

    text-overflow: ellipsis;
    white-space: nowrap;
}

.upload-sub {
    margin-top: 1px;

    color: var(--muted-2);

    font-size: 10px;
}

#f {
    display: none;
}

.run-button {
    min-width: 145px;

    padding: 0 20px;

    border: 0;
    border-radius: 8px;

    background: var(--blue);

    color: #061019;

    font-size: 12px;
    font-weight: 800;

    cursor: pointer;

    transition:
        background 0.15s,
        transform 0.1s,
        opacity 0.15s;
}

.run-button:hover {
    background: #7ac9ff;
}

.run-button:active {
    transform: translateY(1px);
}

.run-button:disabled {
    opacity: 0.5;

    cursor: default;
}

.shortcut {
    margin-top: 8px;

    color: var(--muted-2);

    font-size: 10px;
}


/* =========================================================
   RESULT AREA
   ========================================================= */

#out {
    margin-top: 23px;
}

.panel {
    overflow: hidden;

    border: 1px solid var(--border);
    border-radius: var(--radius);

    background: var(--surface);
}

.panel + .panel {
    margin-top: 13px;
}

.panel-header {
    min-height: 47px;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 16px;

    border-bottom: 1px solid var(--border);
}

.panel-title {
    color: var(--muted);

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.11em;
    text-transform: uppercase;
}

.panel-body {
    padding: 16px;
}


/* =========================================================
   EXECUTION
   ========================================================= */

.timeline {
    position: relative;
}

.timeline::before {
    content: "";

    position: absolute;

    top: 12px;
    bottom: 12px;
    left: 8px;

    width: 1px;

    background: #273440;
}

.step {
    position: relative;

    display: grid;

    grid-template-columns:
        17px
        minmax(0, 1fr)
        auto;

    gap: 12px;

    padding-bottom: 19px;
}

.step:last-child {
    padding-bottom: 0;
}

.step-dot {
    position: relative;

    z-index: 2;

    width: 17px;
    height: 17px;

    margin-top: 2px;

    border: 3px solid var(--surface);

    border-radius: 50%;

    background: var(--green);

    box-shadow:
        0 0 0 1px #2a6341;
}

.step-name {
    color: var(--text);

    font-size: 12px;
    font-weight: 750;
}

.step-detail {
    margin-top: 2px;

    color: var(--muted);

    font-size: 11px;
}

.step-model {
    color: var(--blue);

    font-size: 10px;
    font-weight: 700;

    white-space: nowrap;
}


/* =========================================================
   RESULT
   ========================================================= */

.answer-panel {
    margin-top: 13px;

    overflow: hidden;

    border: 1px solid #285c3d;
    border-radius: var(--radius);

    background:
        linear-gradient(
            135deg,
            rgba(46, 118, 70, 0.09),
            rgba(14, 20, 27, 0.98) 48%
        );
}

.success-title {
    display: flex;
    align-items: center;

    gap: 9px;

    font-size: 13px;
    font-weight: 750;
}

.success-icon {
    width: 21px;
    height: 21px;

    display: grid;
    place-items: center;

    border-radius: 50%;

    background: rgba(69, 212, 123, 0.13);

    color: var(--green);

    font-size: 12px;
}

.answer-content {
    margin-top: 13px;

    color: #dce4eb;

    font-size: 12px;
    line-height: 1.7;

    white-space: pre-wrap;
    word-break: break-word;
}


/* =========================================================
   STRUCTURED FINDINGS
   ========================================================= */

.findings {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.finding-card {
    padding: 13px 14px;

    border: 1px solid var(--border);
    border-radius: 8px;

    background: #0b1118;
}

.finding-top {
    display: flex;
    align-items: center;
    justify-content: space-between;

    gap: 12px;

    margin-bottom: 7px;
}

.finding-item {
    color: var(--text);

    font-size: 12px;
    font-weight: 750;
}

.severity {
    padding: 3px 7px;

    border: 1px solid #5b4b24;
    border-radius: 5px;

    background: rgba(230, 185, 78, 0.08);

    color: var(--yellow);

    font-size: 9px;
    font-weight: 800;

    letter-spacing: 0.06em;
}

.finding-text {
    color: var(--muted);

    font-size: 11px;
}

.finding-recommendation {
    margin-top: 8px;

    color: #a9ddff;

    font-size: 11px;
}

.finding-recommendation::before {
    content: "→ ";

    color: var(--blue);
    font-weight: 800;
}


/* =========================================================
   DOWNLOAD
   ========================================================= */

.download {
    display: inline-flex;
    align-items: center;
    gap: 7px;

    margin-top: 16px;

    padding: 9px 13px;

    border: 1px solid #386b88;
    border-radius: 7px;

    background: #0e202c;

    color: #a9ddff;

    text-decoration: none;

    font-size: 11px;
    font-weight: 750;
}

.download:hover {
    border-color: #4d8eaf;

    background: #132a39;
}


/* =========================================================
   TRACE
   ========================================================= */

.trace {
    margin-top: 13px;

    overflow: hidden;

    border: 1px solid var(--border);
    border-radius: var(--radius);

    background: var(--surface);
}

.trace summary {
    padding: 13px 16px;

    cursor: pointer;

    color: var(--muted);

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.09em;
    text-transform: uppercase;
}

.trace-body {
    padding: 4px 16px 12px;

    border-top: 1px solid var(--border);
}

.trace-item {
    padding: 11px 0;

    border-bottom: 1px solid #202a34;
}

.trace-item:last-child {
    border-bottom: 0;
}

.trace-tool {
    color: var(--blue);

    font-size: 11px;
    font-weight: 750;
}

.trace-code {
    margin-top: 5px;

    color: var(--muted);

    font-family:
        "SFMono-Regular",
        Consolas,
        "Liberation Mono",
        monospace;

    font-size: 10px;
    line-height: 1.55;

    white-space: pre-wrap;
    word-break: break-word;
}


/* =========================================================
   LOADING
   ========================================================= */

.loading {
    display: flex;
    align-items: center;
    gap: 10px;

    color: var(--muted);

    font-size: 12px;
}

.spinner {
    width: 15px;
    height: 15px;

    flex-shrink: 0;

    border: 2px solid #30404f;
    border-top-color: var(--blue);

    border-radius: 50%;

    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}


/* =========================================================
   SYSTEM STATUS
   ========================================================= */

.system-grid {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 9px;
}

.system-item {
    padding: 11px 12px;

    border: 1px solid var(--border);

    border-radius: 8px;

    background: #0b1118;
}

.system-item-title {
    color: var(--muted);

    font-size: 9px;
    font-weight: 700;

    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.system-item-value {
    margin-top: 4px;

    color: var(--green);

    font-size: 11px;
    font-weight: 650;
}


/* =========================================================
   MODEL REGISTRY
   ========================================================= */

.models {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 9px;
}

.model-card {
    padding: 12px;

    border: 1px solid var(--border);

    border-radius: 8px;

    background: #0b1118;
}

.model-card-name {
    color: var(--blue);

    font-size: 11px;
    font-weight: 750;
}

.model-card-role {
    margin-top: 4px;

    color: var(--muted);

    font-size: 10px;
}

.ready {
    display: inline-flex;
    align-items: center;
    gap: 5px;

    margin-top: 8px;

    color: var(--green);

    font-size: 9px;
    font-weight: 700;
}

.ready-dot {
    width: 5px;
    height: 5px;

    border-radius: 50%;

    background: var(--green);
}


/* =========================================================
   ERROR
   ========================================================= */

.error-panel {
    border-color: #633b3b;
}

.error-text {
    color: #ef8c8c;

    font-size: 12px;

    white-space: pre-wrap;
}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {
    display: flex;
    justify-content: center;
    gap: 18px;

    margin-top: 25px;

    color: var(--muted-2);

    font-size: 9px;

    letter-spacing: 0.04em;
}

.footer span {
    display: flex;
    align-items: center;
    gap: 5px;
}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 760px) {

    .header {
        padding: 0 18px;
    }

    .airgap {
        display: none;
    }

    main {
        width: min(100% - 24px, 1080px);

        padding-top: 26px;
    }

    h1 {
        font-size: 25px;
    }

    .controls {
        flex-direction: column;
    }

    .run-button {
        width: 100%;

        min-height: 48px;
    }

    .system-grid,
    .models {
        grid-template-columns: 1fr;
    }

    .step {
        grid-template-columns:
            17px
            minmax(0, 1fr);
    }

    .step-model {
        grid-column: 2;
    }

    .finding-top {
        align-items: flex-start;
        flex-direction: column;
        gap: 5px;
    }
}

</style>
</head>


<body>


<!-- =====================================================
     HEADER
     ===================================================== -->

<header class="header">

    <div class="brand">

        <div class="logo">E</div>

        <div>

            <div class="brand-name">
                EcoLLM
            </div>

            <div class="brand-subtitle">
                SOVEREIGN AI WORKBENCH
            </div>

        </div>

    </div>


    <div class="airgap">

        <span class="airgap-dot"></span>

        LOCAL · AIR-GAPPED

    </div>

</header>



<main>


<!-- =====================================================
     HERO
     ===================================================== -->

<div class="eyebrow">
    Industrial AI · On-Premise
</div>


<h1>
    What should EcoLLM do?
</h1>


<p class="subtitle">
    Execute confidential industrial work locally using
    open-weight multimodal models, agentic tools and
    isolated code execution.
</p>



<!-- =====================================================
     WORKSPACE
     ===================================================== -->

<section class="workspace">

    <div class="section-label">
        Task mode
    </div>


    <div class="modes">

        <button
            class="mode active"
            data-mode="auto"
            onclick="selectMode('auto')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Auto
            </span>
        </button>


        <button
            class="mode"
            data-mode="chat"
            onclick="selectMode('chat')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Chat
            </span>
        </button>


        <button
            class="mode"
            data-mode="analyze"
            onclick="selectMode('analyze')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Analyze
            </span>
        </button>


        <button
            class="mode"
            data-mode="report"
            onclick="selectMode('report')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Report
            </span>
        </button>


        <button
            class="mode"
            data-mode="code"
            onclick="selectMode('code')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Code
            </span>
        </button>


        <button
            class="mode"
            data-mode="knowledge"
            onclick="selectMode('knowledge')"
        >
            <span class="mode-name">
                <span class="mode-dot"></span>
                Knowledge
            </span>
        </button>

    </div>


    <div
        class="mode-description"
        id="modeDescription"
    >
        EcoLLM automatically selects the appropriate local model and tools.
    </div>



    <textarea
        id="q"
        placeholder="Describe the task you want EcoLLM to perform..."
    ></textarea>



    <div class="controls">


        <label
            class="upload"
            id="uploadBox"
            for="f"
        >

            <div class="upload-icon">
                ＋
            </div>


            <div class="upload-copy">

                <div
                    class="upload-title"
                    id="uploadTitle"
                >
                    Attach an industrial document
                </div>


                <div
                    class="upload-sub"
                    id="uploadSub"
                >
                    PDF · scanned reports · images · drawings
                </div>

            </div>

        </label>


        <input
            type="file"
            id="f"
            accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
        >


        <button
            class="run-button"
            id="go"
            onclick="run()"
        >
            Run Agent →
        </button>

    </div>


    <div class="shortcut">
        Ctrl + Enter to run
    </div>

</section>



<!-- =====================================================
     DYNAMIC OUTPUT
     ===================================================== -->

<div id="out"></div>



<!-- =====================================================
     LOCAL MODEL REGISTRY
     ===================================================== -->

<details class="trace" style="margin-top:18px;">

    <summary>
        Local model registry
    </summary>


    <div class="trace-body">

        <div class="models">


            <div class="model-card">

                <div class="model-card-name">
                    Qwen2.5 7B
                </div>

                <div class="model-card-role">
                    General reasoning
                </div>

                <div class="ready">
                    <span class="ready-dot"></span>
                    READY
                </div>

            </div>


            <div class="model-card">

                <div class="model-card-name">
                    Qwen2.5-Coder 7B
                </div>

                <div class="model-card-role">
                    Code generation
                </div>

                <div class="ready">
                    <span class="ready-dot"></span>
                    READY
                </div>

            </div>


            <div class="model-card">

                <div class="model-card-name">
                    Qwen2.5-VL 3B
                </div>

                <div class="model-card-role">
                    Vision · OCR
                </div>

                <div class="ready">
                    <span class="ready-dot"></span>
                    READY
                </div>

            </div>


        </div>

    </div>

</details>



<!-- =====================================================
     SYSTEM STATUS
     ===================================================== -->

<div style="margin-top:13px;">

    <div class="panel">

        <div class="panel-header">

            <div class="panel-title">
                System status
            </div>

        </div>


        <div class="panel-body">

            <div class="system-grid">


                <div class="system-item">

                    <div class="system-item-title">
                        Inference
                    </div>

                    <div class="system-item-value">
                        ● Ollama · Local
                    </div>

                </div>


                <div class="system-item">

                    <div class="system-item-title">
                        Documents
                    </div>

                    <div class="system-item-value">
                        ● On-device OCR / Vision
                    </div>

                </div>


                <div class="system-item">

                    <div class="system-item-title">
                        Code sandbox
                    </div>

                    <div class="system-item-value">
                        ● Docker · Network Disabled
                    </div>

                </div>


            </div>

        </div>

    </div>

</div>



<!-- =====================================================
     FOOTER
     ===================================================== -->

<div class="footer">

    <span>
        ● Ollama local inference
    </span>

    <span>
        ● No external API
    </span>

    <span>
        ● Sandboxed execution
    </span>

    <span>
        ● Loopback only
    </span>

</div>


</main>



<script>


/* =========================================================
   STATE
   ========================================================= */

let selectedMode = "auto";


const MODE_INFO = {

    auto:
        "EcoLLM automatically selects the appropriate local model and tools.",

    chat:
        "General conversation and reasoning using the local general-purpose model.",

    analyze:
        "Analyze documents, scanned reports, images and handwritten material using the vision pipeline.",

    report:
        "Analyze source material and generate a structured Word deliverable.",

    code:
        "Generate and verify code using the local coding model and isolated sandbox.",

    knowledge:
        "Search the organization's local knowledge base and ground the response in internal documents."
};



/* =========================================================
   HELPERS
   ========================================================= */

const $ = s =>
    document.querySelector(s);


function esc(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }


    const d =
        document.createElement("div");


    d.textContent =
        String(value);


    return d.innerHTML;
}


function stringifyAnswer(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }


    if (
        typeof value === "string"
    ) {
        return value;
    }


    try {

        return JSON.stringify(
            value,
            null,
            2
        );

    } catch (e) {

        return String(value);
    }
}


/* =========================================================
   STRUCTURED ANSWER RENDERER
   ========================================================= */

function renderAnswer(value) {

    let obj = value;


    /*
     * The backend may return structured JSON
     * either as an object or as a JSON string.
     */

    if (
        typeof obj === "string"
    ) {

        try {

            obj =
                JSON.parse(obj);

        } catch (e) {

            return `
                <div class="answer-content">
                    ${esc(obj)}
                </div>
            `;
        }
    }


    /*
     * Inspection-analysis result.
     *
     * Example:
     *
     * {
     *   "key_findings": [
     *      {
     *          "item": "...",
     *          "finding": "...",
     *          "severity": "...",
     *          "recommendation": "..."
     *      }
     *   ]
     * }
     */

    if (
        obj &&
        typeof obj === "object" &&
        Array.isArray(obj.key_findings)
    ) {

        let html = `
            <div class="findings">
        `;


        for (
            const finding of obj.key_findings
        ) {

            const severity =
                String(
                    finding.severity ||
                    "INFO"
                ).toUpperCase();


            html += `

                <div class="finding-card">

                    <div class="finding-top">

                        <div class="finding-item">
                            ${esc(
                                finding.item ||
                                "Finding"
                            )}
                        </div>

                        <div class="severity">
                            ${esc(
                                severity
                            )}
                        </div>

                    </div>


                    <div class="finding-text">
                        ${esc(
                            finding.finding ||
                            ""
                        )}
                    </div>


                    ${
                        finding.recommendation
                        ?
                        `
                            <div class="finding-recommendation">
                                ${esc(
                                    finding.recommendation
                                )}
                            </div>
                        `
                        :
                        ""
                    }

                </div>

            `;
        }


        html += `
            </div>
        `;


        return html;
    }


    /*
     * Normal text or other JSON.
     */

    return `
        <div class="answer-content">
            ${esc(
                stringifyAnswer(value)
            )}
        </div>
    `;
}



/* =========================================================
   TASK MODE
   ========================================================= */

function selectMode(mode) {

    selectedMode = mode;


    document
        .querySelectorAll(".mode")
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.mode === mode
            );

        });


    $("#modeDescription").textContent =
        MODE_INFO[mode];


    const prompts = {

        auto:
            "Describe the task you want EcoLLM to perform...",

        chat:
            "Ask a question or describe something you want explained...",

        analyze:
            "Example: Analyze this inspection report and list the key findings...",

        report:
            "Example: Extract the findings and prepare an approval note...",

        code:
            "Example: Calculate the pressure drop and provide verified Python code...",

        knowledge:
            "Example: Find the approved procedure for pump inspection..."
    };


    $("#q").placeholder =
        prompts[mode];
}



/* =========================================================
   PANEL
   ========================================================= */

function panel(
    title,
    body,
    extra = ""
) {

    return `
        <section class="panel ${extra}">

            <div class="panel-header">

                <div class="panel-title">
                    ${title}
                </div>

            </div>

            <div class="panel-body">
                ${body}
            </div>

        </section>
    `;
}



/* =========================================================
   FIND GENERATED FILE
   ========================================================= */

function fileNameFromTrace(trace) {

    for (
        const t of (trace || [])
    ) {

        if (
            t.type === "tool" &&
            t.tool === "write_report" &&
            t.result
        ) {

            const match =
                String(t.result).match(
                    /(?:written to|saved to)\s+(.+\.docx)/i
                );


            if (match) {
                return match[1].trim();
            }
        }
    }


    return null;
}


function outputFileName(path) {

    if (!path) {
        return null;
    }


    path =
        String(path)
            .replaceAll("\\", "/");


    const idx =
        path.lastIndexOf("/");


    return idx >= 0
        ? path.substring(idx + 1)
        : path;
}



/* =========================================================
   EXECUTION TIMELINE
   ========================================================= */

function renderTimeline(data) {

    const trace =
        data.trace || [];


    const steps = [];


    /* Router */

    steps.push({

        name:
            "Model routing",

        detail:
            data.reason ||
            "Task classification",

        model:
            data.model ||
            "Local model"

    });


    /* Tool steps */

    for (
        const t of trace
    ) {

        if (
            t.type !== "tool"
        ) {
            continue;
        }


        if (
            t.tool ===
            "read_document"
        ) {

            steps.push({

                name:
                    "Document analysis",

                detail:
                    "OCR + structured extraction",

                model:
                    "Qwen2.5-VL 3B"

            });

        }


        else if (
            t.tool ===
            "write_report"
        ) {

            steps.push({

                name:
                    "Deliverable generation",

                detail:
                    "Word document created locally",

                model:
                    "Document writer"

            });

        }


        else if (
            t.tool ===
            "run_python"
        ) {

            steps.push({

                name:
                    "Sandbox execution",

                detail:
                    "Python verified with network disabled",

                model:
                    "Docker sandbox"

            });

        }


        else if (
            t.tool ===
            "search_documents"
        ) {

            steps.push({

                name:
                    "Knowledge retrieval",

                detail:
                    "Local document search",

                model:
                    "Local knowledge base"

            });

        }


        else {

            steps.push({

                name:
                    t.tool,

                detail:
                    "Agent tool execution",

                model:
                    ""

            });

        }
    }


    let html =
        `<div class="timeline">`;


    for (
        const s of steps
    ) {

        html += `

            <div class="step">

                <div class="step-dot"></div>

                <div>

                    <div class="step-name">
                        ${esc(s.name)}
                    </div>

                    <div class="step-detail">
                        ${esc(s.detail)}
                    </div>

                </div>

                <div class="step-model">
                    ${esc(s.model)}
                </div>

            </div>

        `;
    }


    html +=
        `</div>`;


    return html;
}



/* =========================================================
   TECHNICAL TRACE
   ========================================================= */

function renderTrace(trace) {

    if (
        !trace ||
        !trace.length
    ) {
        return "";
    }


    let html = `

        <details class="trace">

            <summary>
                View technical agent trace
            </summary>

            <div class="trace-body">

    `;


    for (
        const t of trace
    ) {

        if (
            t.type !== "tool"
        ) {
            continue;
        }


        html += `

            <div class="trace-item">

                <div class="trace-tool">
                    Step ${esc(t.step)}
                    ·
                    ${esc(t.tool)}
                </div>


                <div class="trace-code">

ARGS:

${esc(
    JSON.stringify(
        t.args,
        null,
        2
    )
)}


RESULT:

${esc(t.result)}

                </div>

            </div>

        `;
    }


    html += `

            </div>

        </details>

    `;


    return html;
}



/* =========================================================
   RUN AGENT
   ========================================================= */

async function run() {

    const task =
        $("#q").value.trim();


    if (!task) {

        $("#q").focus();

        return;
    }


    const button =
        $("#go");


    button.disabled =
        true;


    button.textContent =
        "Running…";


    $("#out").innerHTML = `

        <section class="panel">

            <div class="panel-body">

                <div class="loading">

                    <div class="spinner"></div>

                    <span>
                        Routing task and running locally…
                    </span>

                </div>

            </div>

        </section>

    `;


    const fd =
        new FormData();


    /*
     * Task mode is sent as a routing hint.
     * The backend remains responsible for actual model selection.
     */

    fd.append(
        "task",
        `[Task mode: ${selectedMode}] ${task}`
    );


    const file =
        $("#f").files[0];


    if (file) {

        fd.append(
            "file",
            file
        );
    }


    try {

        const response =
            await fetch(
                "/api/run",
                {
                    method: "POST",
                    body: fd
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
        ) {

            throw new Error(
                data.answer ||
                "Server returned an error."
            );
        }


        /*
         * Render structured results such as
         * key_findings as UI cards instead of raw JSON.
         */

        const answer =
            renderAnswer(
                data.answer
            );


        /* Execution panel */

        let html =
            panel(
                "Agent execution",
                renderTimeline(data)
            );


        /* Generated file */

        const filePath =
            fileNameFromTrace(
                data.trace
            );


        const fileName =
            outputFileName(
                filePath
            );


        /* Result */

        let answerBody = `

            <div class="success-title">

                <span class="success-icon">
                    ✓
                </span>

                <span>
                    Task completed successfully
                </span>

            </div>


            <div style="margin-top:14px;">
                ${answer}
            </div>

        `;


        if (fileName) {

            answerBody += `

                <a
                    class="download"
                    href="/output/${encodeURIComponent(fileName)}"
                    download
                >
                    ↓
                    Download Word document
                </a>

            `;
        }


        html += `

            <section class="answer-panel">

                <div class="panel-body">

                    ${answerBody}

                </div>

            </section>

        `;


        html +=
            renderTrace(
                data.trace
            );


        $("#out").innerHTML =
            html;


    }

    catch (e) {

        $("#out").innerHTML = `

            <section class="panel error-panel">

                <div class="panel-header">

                    <div class="panel-title">
                        Execution error
                    </div>

                </div>


                <div class="panel-body">

                    <div class="error-text">
                        ${esc(
                            e.message || e
                        )}
                    </div>

                </div>

            </section>

        `;

    }

    finally {

        button.disabled =
            false;

        button.textContent =
            "Run Agent →";
    }
}



/* =========================================================
   FILE INPUT
   ========================================================= */

$("#f").addEventListener(
    "change",
    function () {

        const file =
            this.files[0];


        if (!file) {
            return;
        }


        $("#uploadBox")
            .classList
            .add("has-file");


        $("#uploadTitle")
            .textContent =
            file.name;


        $("#uploadSub")
            .textContent =
            `${(
                file.size / 1024
            ).toFixed(1)} KB · Ready`;
    }
);



/* =========================================================
   KEYBOARD SHORTCUT
   ========================================================= */

$("#q").addEventListener(
    "keydown",
    e => {

        if (
            e.key === "Enter" &&
            (e.metaKey || e.ctrlKey)
        ) {

            run();
        }
    }
);

</script>

</body>
</html>
"""


def parse_multipart(body: bytes, boundary: bytes):
    """
    Tiny multipart parser.
    Enough for one text field and one file.
    """

    fields = {}
    files = {}

    for part in body.split(
        b"--" + boundary
    ):

        if (
            b"\r\n\r\n"
            not in part
        ):
            continue

        head, data = part.split(
            b"\r\n\r\n",
            1
        )

        data = data.rstrip(
            b"\r\n-"
        )

        head = head.decode(
            "utf-8",
            "ignore"
        )

        if 'name="' not in head:
            continue

        name = (
            head
            .split(
                'name="',
                1
            )[1]
            .split(
                '"',
                1
            )[0]
        )

        if 'filename="' in head:

            fn = (
                head
                .split(
                    'filename="',
                    1
                )[1]
                .split(
                    '"',
                    1
                )[0]
            )

            if fn:

                files[name] = (
                    fn,
                    data
                )

        else:

            fields[name] = data.decode(
                "utf-8",
                "ignore"
            )

    return fields, files


def kind_of(filename: str) -> str:

    ext = os.path.splitext(
        filename
    )[1].lower()

    if ext in (
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp"
    ):

        return "image"

    if ext == ".pdf":

        return "pdf"

    return "text"


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *a):
        """
        Keep the demo terminal clean.
        """
        pass


    def _send(
        self,
        code,
        body,
        ctype,
        extra_headers=None
    ):

        self.send_response(code)

        self.send_header(
            "Content-Type",
            ctype
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        if extra_headers:

            for key, value in extra_headers.items():

                self.send_header(
                    key,
                    value
                )

        self.end_headers()

        self.wfile.write(
            body
        )


    def do_GET(self):

        # Main UI

        if self.path in (
            "/",
            "/index.html"
        ):

            return self._send(
                200,
                PAGE.encode(),
                "text/html; charset=utf-8"
            )


        # Generated Word files

        if self.path.startswith(
            "/output/"
        ):

            requested = unquote(
                self.path[
                    len("/output/"):
                ]
            )

            filename = os.path.basename(
                requested
            )

            # Prevent directory traversal.
            if (
                filename != requested
                or not filename
                or not filename.lower().endswith(
                    ".docx"
                )
            ):

                return self._send(
                    403,
                    b"forbidden",
                    "text/plain"
                )

            path = os.path.join(
                OUTPUT,
                filename
            )

            if not os.path.isfile(
                path
            ):

                return self._send(
                    404,
                    b"file not found",
                    "text/plain"
                )

            try:

                with open(
                    path,
                    "rb"
                ) as fh:

                    data = fh.read()

                return self._send(
                    200,
                    data,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    {
                        "Content-Disposition":
                            f'attachment; filename="{filename}"'
                    }
                )

            except Exception:

                return self._send(
                    500,
                    b"could not read file",
                    "text/plain"
                )


        return self._send(
            404,
            b"not found",
            "text/plain"
        )


    def do_POST(self):

        if self.path != "/api/run":

            return self._send(
                404,
                b"not found",
                "text/plain"
            )

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                length
            )

            ctype = self.headers.get(
                "Content-Type",
                ""
            )

            boundary = ctype.split(
                "boundary="
            )[-1].encode()

            fields, files = parse_multipart(
                body,
                boundary
            )

            task = fields.get(
                "task",
                ""
            )

            has_file = False
            file_kind = ""

            if "file" in files:

                fn, data = files["file"]

                os.makedirs(
                    UPLOADS,
                    exist_ok=True
                )

                path = os.path.join(
                    UPLOADS,
                    os.path.basename(fn)
                )

                with open(
                    path,
                    "wb"
                ) as fh:

                    fh.write(data)

                has_file = True

                file_kind = kind_of(fn)

                task = (
                    f"{task}\n\n"
                    f"[Attached file saved at: {path}]"
                )

            result = agent.run(
                task,
                has_file,
                file_kind
            )

        except Exception:

            traceback.print_exc()

            r = route(
                "",
                False,
                ""
            )

            result = {

                "answer":
                    "Server error -- see terminal.",

                "model":
                    r.model,

                "reason":
                    "n/a",

                "trace":
                    []

            }

        self._send(
            200,
            json.dumps(
                result,
                default=str
            ).encode(),
            "application/json"
        )


if __name__ == "__main__":

    print(
        f"Workbench on http://localhost:{PORT}"
        f"  (bound to loopback only)"
    )

    HTTPServer(
        ("127.0.0.1", PORT),
        Handler
    ).serve_forever()