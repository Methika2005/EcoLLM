import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

import agent
from router import route
from orchestrator.workflow import WorkflowQueue, WorkItem


PORT = 8080
UPLOADS = "uploads"
OUTPUT = "output"


PAGE = r"""<!doctype html>
<html lang="en">
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>EcoLLM - Sovereign AI Workbench</title>

<style>

:root {
    --bg: #080c11;
    --surface: #0e141b;
    --surface2: #121a23;
    --border: #26323e;
    --text: #e8edf3;
    --muted: #8996a5;
    --blue: #55b9ff;
    --green: #45d47b;
    --yellow: #e6b94e;
    --red: #ef6a6a;
}

* {
    box-sizing: border-box;
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
        system-ui,
        -apple-system,
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
}

.brand-name {
    font-size: 17px;
    font-weight: 750;
}

.brand-subtitle {
    color: var(--muted);

    font-size: 10px;

    letter-spacing: 0.03em;
}

.airgap {
    padding: 7px 12px;

    border: 1px solid #285c3c;
    border-radius: 999px;

    background: rgba(52, 132, 78, 0.08);

    color: #78e59f;

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.08em;
}

.airgap-dot,
.ready-dot {
    display: inline-block;

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--green);

    margin-right: 6px;
}


/* =========================================================
   MAIN
   ========================================================= */

main {
    width: min(1080px, calc(100% - 40px));

    margin: auto;

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
    margin: 7px 0;

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

.workspace,
.panel {
    border: 1px solid var(--border);
    border-radius: 10px;

    background: var(--surface);
}

.workspace {
    padding: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(18, 27, 37, 0.96),
            rgba(12, 17, 24, 0.98)
        );
}

.section-label,
.panel-title {
    color: var(--muted);

    font-size: 10px;
    font-weight: 750;

    letter-spacing: 0.11em;

    text-transform: uppercase;
}


/* =========================================================
   MODES
   ========================================================= */

.modes {
    display: flex;

    gap: 7px;

    flex-wrap: wrap;

    margin: 9px 0 15px;
}

.mode {
    padding: 7px 13px;

    border: 1px solid #334252;
    border-radius: 7px;

    background: #0b1118;

    color: var(--muted);

    font-size: 11px;
    font-weight: 650;

    cursor: pointer;
}

.mode.active {
    border-color: #397da7;

    background: #102535;

    color: #9bd8ff;
}

.mode-dot {
    display: inline-block;

    width: 5px;
    height: 5px;

    border-radius: 50%;

    background: currentColor;

    margin-right: 6px;
}

.mode-description {
    margin-bottom: 14px;

    color: #5e6b79;

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

    outline: 0;

    border: 1px solid #334252;
    border-radius: 8px;

    background: #090e14;

    color: var(--text);

    font-size: 14px;
}

textarea::placeholder {
    color: #596575;
}

textarea:focus {
    border-color: #397da7;
}


/* =========================================================
   UPLOAD
   ========================================================= */

.controls {
    display: flex;

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

.upload-title {
    overflow: hidden;

    font-size: 12px;
    font-weight: 650;

    text-overflow: ellipsis;
    white-space: nowrap;
}

.upload-sub {
    color: #5e6b79;

    font-size: 10px;
}

#f {
    display: none;
}


/* =========================================================
   RUN BUTTON
   ========================================================= */

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
}

.run-button:disabled {
    opacity: 0.5;
}

.shortcut {
    margin-top: 8px;

    color: #5e6b79;

    font-size: 10px;
}


/* =========================================================
   RESULT
   ========================================================= */

#out {
    margin-top: 23px;
}

.panel + .panel {
    margin-top: 13px;
}

.panel-header {
    min-height: 47px;

    display: flex;
    align-items: center;

    padding: 0 16px;

    border-bottom: 1px solid var(--border);
}

.panel-body {
    padding: 16px;
}


/* =========================================================
   TIMELINE
   ========================================================= */

.timeline {
    position: relative;
}

.timeline:before {
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

.step-dot {
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
    font-size: 12px;
    font-weight: 750;
}

.step-detail {
    color: var(--muted);

    font-size: 11px;
}

.step-model {
    color: var(--blue);

    font-size: 10px;
    font-weight: 700;
}


/* =========================================================
   ANSWER
   ========================================================= */

.answer-panel {
    margin-top: 13px;

    border: 1px solid #285c3d;
    border-radius: 10px;

    background:
        linear-gradient(
            135deg,
            rgba(46, 118, 70, 0.09),
            rgba(14, 20, 27, 0.98) 48%
        );
}

.answer-content {
    margin-top: 13px;

    color: #dce4eb;

    font-size: 12px;

    line-height: 1.7;

    white-space: pre-wrap;

    word-break: break-word;
}

.success-title {
    font-size: 13px;

    font-weight: 750;
}


/* =========================================================
   FINDINGS
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

    justify-content: space-between;

    gap: 12px;

    margin-bottom: 7px;
}

.finding-item {
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
}

.finding-text,
.finding-recommendation {
    font-size: 11px;
}

.finding-text {
    color: var(--muted);
}

.finding-recommendation {
    margin-top: 8px;

    color: #a9ddff;
}


/* =========================================================
   DOWNLOAD
   ========================================================= */

.download {
    display: inline-block;

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


/* =========================================================
   TRACE
   ========================================================= */

.trace {
    margin-top: 13px;

    overflow: hidden;

    border: 1px solid var(--border);

    border-radius: 10px;

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

.trace-tool {
    color: var(--blue);

    font-size: 11px;

    font-weight: 750;
}

.trace-code {
    margin-top: 5px;

    color: var(--muted);

    font:
        10px/1.55
        Consolas,
        monospace;

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
   STATUS / MODELS
   ========================================================= */

.system-grid,
.models {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 9px;
}

.system-item,
.model-card {
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

.system-item-value,
.ready {
    margin-top: 4px;

    color: var(--green);

    font-size: 10px;

    font-weight: 650;
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

    color: #5e6b79;

    font-size: 9px;
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
        width: calc(100% - 24px);

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
    }

}

</style>

</head>


<body>


<header class="header">

    <div class="brand">

        <div class="logo">
            E
        </div>

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

        LOCAL · LOOPBACK

    </div>

</header>


<main>


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
            <span class="mode-dot"></span>
            Auto
        </button>


        <button
            class="mode"
            data-mode="chat"
            onclick="selectMode('chat')"
        >
            <span class="mode-dot"></span>
            Chat
        </button>


        <button
            class="mode"
            data-mode="analyze"
            onclick="selectMode('analyze')"
        >
            <span class="mode-dot"></span>
            Analyze
        </button>


        <button
            class="mode"
            data-mode="report"
            onclick="selectMode('report')"
        >
            <span class="mode-dot"></span>
            Report
        </button>


        <button
            class="mode"
            data-mode="code"
            onclick="selectMode('code')"
        >
            <span class="mode-dot"></span>
            Code
        </button>


        <button
            class="mode"
            data-mode="workflow"
            onclick="selectMode('workflow')"
        >
            <span class="mode-dot"></span>
            Workflow
        </button>


        <button
            class="mode"
            data-mode="knowledge"
            onclick="selectMode('knowledge')"
        >
            <span class="mode-dot"></span>
            Knowledge
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
                ↑
            </div>


            <div>

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
            multiple
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


<div id="out"></div>


<details
    class="trace"
    style="margin-top:18px"
>

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
                    ● READY
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
                    ● READY
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
                    ● READY
                </div>

            </div>


        </div>

    </div>

</details>


<div style="margin-top:13px">

    <section class="panel">

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

    </section>

</div>


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

    workflow:
        "Process multiple industrial reports through AI triage, priority ordering and human-review actions.",

    knowledge:
        "Search the organization local knowledge base and ground the response in internal documents."

};


/* =========================================================
   HELPERS
   ========================================================= */

const $ = s =>
    document.querySelector(s);


function esc(value) {

    const d =
        document.createElement("div");

    d.textContent =
        value == null
            ? ""
            : String(value);

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
   ANSWER RENDERING
   ========================================================= */

function renderAnswer(value) {

    let obj = value;


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


    if (
        obj &&
        typeof obj === "object" &&
        Array.isArray(obj.key_findings)
    ) {

        let html =
            '<div class="findings">';


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
                            ${esc(severity)}
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
                            ? `
                                <div class="finding-recommendation">
                                    ${esc(
                                        finding.recommendation
                                    )}
                                </div>
                              `
                            : ""
                    }

                </div>

            `;

        }


        html +=
            "</div>";


        return html;

    }


    return `

        <div class="answer-content">

            ${esc(
                stringifyAnswer(value)
            )}

        </div>

    `;

}


/* =========================================================
   MODE SELECTION
   ========================================================= */

function selectMode(mode) {

    selectedMode =
        mode;


    document
        .querySelectorAll(".mode")
        .forEach(
            button => {

                button.classList.toggle(
                    "active",
                    button.dataset.mode === mode
                );

            }
        );


    $("#modeDescription").textContent =
        MODE_INFO[mode] ||
        MODE_INFO.auto;


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

        workflow:
            "Example: Triage these industrial reports and flag high-priority cases for human review...",

        knowledge:
            "Example: Find the approved procedure for pump inspection..."

    };


    $("#q").placeholder =
        prompts[mode] ||
        prompts.auto;


    $("#f").multiple =
        mode === "workflow";

}


/* =========================================================
   PANEL
   ========================================================= */

function panel(
    title,
    body
) {

    return `

        <section class="panel">

            <div class="panel-header">

                <div class="panel-title">
                    ${esc(title)}
                </div>

            </div>

            <div class="panel-body">

                ${body}

            </div>

        </section>

    `;

}


/* =========================================================
   GENERATED FILE
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
                String(
                    t.result
                ).match(
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
            .replaceAll(
                "\\",
                "/"
            );


    const index =
        path.lastIndexOf("/");


    return index >= 0
        ? path.substring(index + 1)
        : path;

}


/* =========================================================
   TIMELINE
   ========================================================= */

function renderTimeline(data) {

    if (data.workflow) {

        const results =
            data.results || [];


        const steps = [

            {
                name:
                    "Workflow queue",

                detail:
                    "Multiple reports received and prioritized",

                model:
                    "Workflow Orchestrator"
            },

            {
                name:
                    "AI triage",

                detail:
                    "Priority assigned from extracted findings",

                model:
                    "Qwen2.5 7B"
            },

            {
                name:
                    "Action execution",

                detail:
                    results.length +
                    " prioritized item(s) processed",

                model:
                    "Local tools"
            }

        ];


        return `

            <div class="timeline">

                ${
                    steps
                        .map(
                            step => `

                                <div class="step">

                                    <div class="step-dot"></div>

                                    <div>

                                        <div class="step-name">
                                            ${esc(step.name)}
                                        </div>

                                        <div class="step-detail">
                                            ${esc(step.detail)}
                                        </div>

                                    </div>

                                    <div class="step-model">
                                        ${esc(step.model)}
                                    </div>

                                </div>

                            `
                        )
                        .join("")
                }

            </div>

        `;

    }


    const trace =
        data.trace || [];


    const steps = [

        {

            name:
                "Model routing",

            detail:
                data.reason ||
                "Task classification",

            model:
                data.model ||
                "Local model"

        }

    ];


    for (
        const t of trace
    ) {

        if (
            t.type !== "tool"
        ) {
            continue;
        }


        const map = {

            read_document: [
                "Document analysis",
                "OCR + structured extraction",
                "Qwen2.5-VL 3B"
            ],

            write_report: [
                "Deliverable generation",
                "Word document created locally",
                "Document writer"
            ],

            run_python: [
                "Sandbox execution",
                "Python verified with network disabled",
                "Docker sandbox"
            ],

            search_documents: [
                "Knowledge retrieval",
                "Local document search",
                "Local knowledge base"
            ]

        };


        const mapped =
            map[t.tool] ||
            [
                t.tool,
                "Agent tool execution",
                ""
            ];


        steps.push({

            name:
                mapped[0],

            detail:
                mapped[1],

            model:
                mapped[2]

        });

    }


    return `

        <div class="timeline">

            ${
                steps
                    .map(
                        step => `

                            <div class="step">

                                <div class="step-dot"></div>

                                <div>

                                    <div class="step-name">
                                        ${esc(step.name)}
                                    </div>

                                    <div class="step-detail">
                                        ${esc(step.detail)}
                                    </div>

                                </div>

                                <div class="step-model">
                                    ${esc(step.model)}
                                </div>

                            </div>

                        `
                    )
                    .join("")
            }

        </div>

    `;

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

                    Step
                    ${esc(t.step)}

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
   WORKFLOW RESULT
   ========================================================= */

function renderWorkflow(data) {

    const results =
        data.results || [];


    const alerts =
        data.alerts || [];


    let html = `

        <section class="answer-panel">

            <div class="panel-body">

                <div class="success-title">
                    ✓ Workflow completed
                </div>


                <div class="answer-content">

                    ${esc(
                        (
                            data.answer &&
                            data.answer.summary
                        ) ||
                        "Reports processed through the local workflow queue."
                    )}

                </div>

    `;


    /* =====================================================
       HUMAN REVIEW ALERTS
       ===================================================== */

    if (alerts.length) {

        html += `

            <div style="margin-top:15px">

                <div class="section-label">
                    Human review alerts
                </div>

        `;


        for (const alert of alerts) {

            html += `

                <div
                    class="finding-card"
                    style="margin-top:8px"
                >

                    <div class="finding-top">

                        <div class="finding-item">

                            🚨 ${esc(
                                alert.report_name ||
                                alert.item_id ||
                                "Inspection report"
                            )}

                        </div>


                        <div class="severity">

                            ${esc(
                                alert.priority ||
                                "HIGH"
                            )}

                        </div>

                    </div>


                    <div class="finding-text">

                        ${esc(
                            alert.message ||
                            "High-priority finding requires human review."
                        )}

                    </div>


                    ${
                        alert.required_action
                            ? `
                                <div class="finding-recommendation">

                                    Required action:
                                    ${esc(
                                        alert.required_action
                                    )}

                                </div>
                              `
                            : ""
                    }

                </div>

            `;

        }


        html += "</div>";

    }


    /* =====================================================
       INSPECTION RESULTS
       ===================================================== */

    html += `

        <div style="margin-top:15px">

            <div class="section-label">
                Inspection results
            </div>

    `;


    for (const result of results) {

        const reportName =
            result.report_name ||
            result.filename ||
            "Inspection report";


        const summary =
            result.summary ||
            "No summary was returned for this report.";


        const priority =
            result.priority ||
            "NOT ASSESSED";


        const action =
            result.action ||
            "";


        const status =
            result.status ||
            "";


        const reason =
            result.reason ||
            "";


        const requiredAction =
            result.required_action ||
            "";


        /* =================================================
           WORD DOCUMENT DOWNLOAD
           ================================================= */

        const execution =
            String(
                result.execution || ""
            );


        const docMatch =
            execution.match(
                /(?:written to|saved to)\s+(.+\.docx)/i
            );


        let docFileName = null;


        if (docMatch) {

            const docPath =
                docMatch[1]
                    .trim()
                    .replaceAll("\\", "/");


            const slashIndex =
                docPath.lastIndexOf("/");


            docFileName =
                slashIndex >= 0
                    ? docPath.substring(
                        slashIndex + 1
                    )
                    : docPath;

        }


        html += `

            <div
                class="finding-card"
                style="margin-top:8px"
            >

                <div class="finding-top">

                    <div class="finding-item">

                        ${esc(reportName)}

                    </div>


                    <div class="severity">

                        ${esc(priority)}

                    </div>

                </div>


                <!-- ACTUAL INSPECTION SUMMARY -->

                <div
                    class="finding-text"
                    style="margin-top:12px"
                >

                    <strong>
                        Inspection Summary
                    </strong>


                    <div style="margin-top:8px">

                        ${esc(summary)}

                    </div>

                </div>


                <!-- AI ASSESSMENT -->

                ${
                    reason
                        ? `
                            <div
                                class="finding-text"
                                style="margin-top:12px"
                            >

                                <strong>
                                    Assessment
                                </strong>


                                <div style="margin-top:6px">

                                    ${esc(reason)}

                                </div>

                            </div>
                          `
                        : ""
                }


                <!-- REQUIRED ACTION -->

                ${
                    requiredAction
                        ? `
                            <div
                                class="finding-recommendation"
                                style="margin-top:10px"
                            >

                                <strong>
                                    Required Action
                                </strong>


                                <div style="margin-top:6px">

                                    ${esc(
                                        requiredAction
                                    )}

                                </div>

                            </div>
                          `
                        : ""
                }


                <!-- WORKFLOW DECISION -->

                ${
                    action
                        ? `
                            <div
                                class="finding-text"
                                style="margin-top:10px"
                            >

                                <strong>
                                    Workflow Action:
                                </strong>

                                ${esc(action)}

                                ${
                                    status
                                        ? `
                                            ·
                                            <strong>
                                                Status:
                                            </strong>

                                            ${esc(status)}
                                          `
                                        : ""
                                }

                            </div>
                          `
                        : ""
                }


                <!-- WORD DOWNLOAD -->

                ${
                    docFileName
                        ? `
                            <a
                                class="download"
                                href="/output/${encodeURIComponent(docFileName)}"
                                download
                                style="display:inline-block;margin-top:12px;"
                            >

                                ↓ Download
                                ${esc(docFileName)}

                            </a>
                          `
                        : ""
                }

            </div>

        `;

    }


    html += `

        </div>

        </div>

        </section>

    `;


    return html;

}

/* =========================================================
   RUN
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
        "Running...";


    $("#out").innerHTML = `

        <section class="panel">

            <div class="panel-body">

                <div class="loading">

                    <div class="spinner"></div>

                    <span>
                        Routing task and running locally...
                    </span>

                </div>

            </div>

        </section>

    `;


    const fd =
        new FormData();


    fd.append(
        "task",
        task
    );


    fd.append(
        "mode",
        selectedMode
    );


    const files =
        Array.from(
            $("#f").files
        );


    if (
        selectedMode === "workflow"
    ) {

        for (
            const file of files
        ) {

            fd.append(
                "file",
                file
            );

        }

    } else if (
        files[0]
    ) {

        fd.append(
            "file",
            files[0]
        );

    }


    try {

        const response =
            await fetch(
                "/api/run",
                {
                    method:
                        "POST",

                    body:
                        fd
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


        if (
            data.workflow
        ) {

            $("#out").innerHTML =

                panel(
                    "Workflow execution",
                    renderTimeline(data)
                )

                +

                renderWorkflow(data);

            return;

        }


        let html =
            panel(
                "Agent execution",
                renderTimeline(data)
            );


        const fileName =
            outputFileName(
                fileNameFromTrace(
                    data.trace
                )
            );


        let answerBody = `

            <div class="success-title">

                ✓ Task completed successfully

            </div>


            <div style="margin-top:14px">

                ${renderAnswer(data.answer)}

            </div>

        `;


        if (
            fileName
        ) {

            answerBody += `

                <a
                    class="download"
                    href="/output/${encodeURIComponent(fileName)}"
                    download
                >
                    ↓ Download Word document
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


    } catch (e) {

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

    } finally {

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

        const files =
            Array.from(
                this.files
            );


        if (!files.length) {

            return;

        }


        $("#uploadBox")
            .classList
            .add("has-file");


        if (
            selectedMode === "workflow" &&
            files.length > 1
        ) {

            $("#uploadTitle")
                .textContent =
                files.length +
                " industrial reports selected";


            $("#uploadSub")
                .textContent =
                files
                    .map(
                        file => file.name
                    )
                    .join(" · ");

        } else {

            $("#uploadTitle")
                .textContent =
                files[0].name;


            $("#uploadSub")
                .textContent =
                (
                    files[0].size /
                    1024
                ).toFixed(1) +
                " KB · Ready";

        }

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


selectMode("auto");

</script>

</body>
</html>
"""


# =========================================================
# MULTIPART PARSER
# =========================================================


def parse_multipart(body: bytes, boundary: bytes):

    fields = {}
    files = {}

    delimiter = b"--" + boundary

    for part in body.split(delimiter):
        if b"\r\n\r\n" not in part:
            continue

        head, data = part.split(b"\r\n\r\n", 1)

        data = data.rstrip(b"\r\n-")

        head = head.decode("utf-8", "ignore")

        if 'name="' not in head:
            continue

        name = head.split('name="', 1)[1].split('"', 1)[0]

        if 'filename="' in head:
            filename = head.split('filename="', 1)[1].split('"', 1)[0]

            if filename:
                files.setdefault(name, []).append((filename, data))

        else:
            fields[name] = data.decode("utf-8", "ignore")

    return fields, files


# =========================================================
# FILE TYPE
# =========================================================


def kind_of(filename: str) -> str:

    ext = os.path.splitext(filename)[1].lower()

    if ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        return "image"

    if ext == ".pdf":
        return "pdf"

    return "text"


# =========================================================
# ANSWER CONVERSION
# =========================================================


def answer_to_text(answer) -> str:

    if answer is None:
        return ""

    if isinstance(answer, str):
        return answer

    try:
        return json.dumps(answer, indent=2, default=str)

    except Exception:
        return str(answer)


# =========================================================
# WORKFLOW
# =========================================================


def run_workflow(uploaded_files, user_task):

    queue = WorkflowQueue()

    extracted_reports = {}

    uploaded_items = []

    os.makedirs(UPLOADS, exist_ok=True)

    os.makedirs(OUTPUT, exist_ok=True)

    user_task_lower = (user_task or "").strip().lower()

    # -----------------------------------------------------
    # UNDERSTAND USER INTENT
    # -----------------------------------------------------

    summary_keywords = (
        "summary",
        "summarize",
        "summarise",
        "overview",
        "brief",
        "give me a summary",
        "summarize this",
        "summarise this",
    )

    report_keywords = (
        "word",
        "document",
        "approval note",
        "generate a report",
        "create a report",
        "write a report",
        "prepare a report",
        "generate report",
        "create report",
    )

    wants_summary = any(keyword in user_task_lower for keyword in summary_keywords)

    wants_report = any(keyword in user_task_lower for keyword in report_keywords)

    # -----------------------------------------------------
    # SAVE ALL REPORTS
    # -----------------------------------------------------

    for index, uploaded in enumerate(uploaded_files, start=1):
        filename, data = uploaded

        safe_name = os.path.basename(filename)

        path = os.path.join(UPLOADS, safe_name)

        with open(path, "wb") as fh:
            fh.write(data)

        # Internal ID only.
        item_id = f"R{index:03d}"

        queue.add(WorkItem(id=item_id, file_path=path))

        report_name = os.path.splitext(safe_name)[0]

        uploaded_items.append(
            {
                "id": item_id,
                "filename": safe_name,
                "report_name": report_name,
                "path": path,
            }
        )

    # -----------------------------------------------------
    # DOCUMENT ANALYSIS
    # -----------------------------------------------------

    for item in queue.get_all():
        report_name = os.path.splitext(os.path.basename(item.file_path))[0]

        analysis_task = (
            "Analyze this industrial inspection report "
            "and answer the user's request.\n\n"
            "The user request is:\n"
            f"{user_task}\n\n"
            "First, identify the actual information contained "
            "in the inspection document.\n"
            "Do not invent information.\n"
            "Do not assume missing values.\n"
            "Use only information supported by the document.\n\n"
            "For a summary request, provide a concise but useful "
            "inspection summary containing:\n"
            "1. Equipment or subject inspected, if available\n"
            "2. Inspection status or overall condition, if available\n"
            "3. Key findings and observations\n"
            "4. Abnormalities or issues found\n"
            "5. Recommended actions, if stated or clearly supported\n\n"
            "For each important finding, preserve the actual "
            "details from the document.\n\n"
            f"Report name: {report_name}\n"
            f"Attached file: {item.file_path}"
        )

        analysis = agent.run(analysis_task, True, kind_of(item.file_path))

        extracted_reports[item.id] = answer_to_text(analysis.get("answer", ""))

    # -----------------------------------------------------
    # AI TRIAGE
    # -----------------------------------------------------

    for item in queue.get_all():
        queue.triage_item(item.id, extracted_reports.get(item.id, ""))

    # -----------------------------------------------------
    # EXECUTION
    # -----------------------------------------------------

    if wants_report and not wants_summary:
        # Only generate Word documents when the
        # user explicitly asks for a report/document.
        results = queue.process_prioritized(extracted_reports)

    else:
        # Summary / analysis request:
        # return the useful extracted information
        # without automatically generating a Word document.

        results = []

        for item in queue.get_all():
            report_name = os.path.splitext(os.path.basename(item.file_path))[0]

            priority = item.priority

            action = (
                "ALERT_AND_HUMAN_REVIEW"
                if priority == "HIGH"
                else "FLAG_FOR_REVIEW"
                if priority == "MEDIUM"
                else "RECORD_AND_MONITOR"
                if priority == "LOW"
                else "HUMAN_REVIEW"
            )

            # High-priority findings still trigger
            # the alerting mechanism even when the
            # user only requested a summary.
            if priority == "HIGH":
                queue.create_alert(item.id)

            results.append(
                {
                    "id": item.id,
                    "report_name": report_name,
                    "priority": priority,
                    "action": action,
                    "status": item.status,
                    "summary": extracted_reports.get(item.id, ""),
                    "reason": item.reason,
                    "required_action": item.required_action,
                }
            )

    # -----------------------------------------------------
    # ALERTS
    # -----------------------------------------------------

    name_by_id = {item["id"]: item["report_name"] for item in uploaded_items}

    alerts = []

    for alert in queue.get_alerts():
        alerts.append(
            {
                "item_id": alert.item_id,
                "report_name": name_by_id.get(alert.item_id, alert.item_id),
                "priority": alert.priority,
                "message": alert.message,
                "required_action": alert.required_action,
                "status": alert.status,
            }
        )

    # -----------------------------------------------------
    # RESPONSE SUMMARY
    # -----------------------------------------------------

    if wants_report and not wants_summary:
        summary_text = (
            f"Processed "
            f"{len(uploaded_files)} "
            f"industrial report"
            f"{'s' if len(uploaded_files) != 1 else ''} "
            f"and generated the requested deliverable."
        )

    else:
        summary_text = (
            f"Analyzed "
            f"{len(uploaded_files)} "
            f"industrial report"
            f"{'s' if len(uploaded_files) != 1 else ''} "
            f"and prepared the requested summary."
        )

    return {
        "workflow": True,
        "answer": {
            "summary": summary_text,
            "results": results,
        },
        "items": uploaded_items,
        "results": results,
        "alerts": alerts,
        "model": "Workflow Orchestrator",
        "reason": ("Document analysis → AI triage → intent-based workflow action"),
        "trace": [],
    }


# =========================================================
# HTTP SERVER
# =========================================================


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):

        pass

    # -----------------------------------------------------
    # SEND RESPONSE
    # -----------------------------------------------------

    def _send(self, code, body, ctype, extra_headers=None):

        self.send_response(code)

        self.send_header("Content-Type", ctype)

        self.send_header("Content-Length", str(len(body)))

        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.end_headers()

        self.wfile.write(body)

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    def do_GET(self):

        # Main UI
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")

        # Generated Word documents
        if self.path.startswith("/output/"):
            requested = unquote(self.path[len("/output/") :])

            filename = os.path.basename(requested)

            # Prevent directory traversal
            if (
                filename != requested
                or not filename
                or not filename.lower().endswith(".docx")
            ):
                return self._send(403, b"forbidden", "text/plain")

            path = os.path.join(OUTPUT, filename)

            if not os.path.isfile(path):
                return self._send(404, b"file not found", "text/plain")

            try:
                with open(path, "rb") as fh:
                    data = fh.read()

                return self._send(
                    200,
                    data,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    {"Content-Disposition": f'attachment; filename="{filename}"'},
                )

            except Exception:
                traceback.print_exc()

                return self._send(500, b"could not read file", "text/plain")

        return self._send(404, b"not found", "text/plain")

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    def do_POST(self):

        if self.path != "/api/run":
            return self._send(404, b"not found", "text/plain")

        try:
            length = int(self.headers.get("Content-Length", "0"))

            body = self.rfile.read(length)

            content_type = self.headers.get("Content-Type", "")

            if "boundary=" not in content_type:
                raise ValueError("Invalid request: multipart boundary missing.")

            boundary = (
                content_type.split("boundary=", 1)[1].strip().strip('"').encode("utf-8")
            )

            fields, files = parse_multipart(body, boundary)

            task = fields.get("task", "")

            mode = fields.get("mode", "auto").lower()

            uploaded_files = files.get("file", [])

            # -------------------------------------------------
            # WORKFLOW MODE
            # -------------------------------------------------

            if mode == "workflow":
                if not uploaded_files:
                    result = {
                        "workflow": True,
                        "answer": {
                            "summary": "No industrial reports were uploaded.",
                            "results": [],
                        },
                        "items": [],
                        "results": [],
                        "alerts": [],
                        "model": "Workflow Orchestrator",
                        "reason": "Workflow requires uploaded reports.",
                        "trace": [],
                    }

                else:
                    result = run_workflow(uploaded_files, task)

                return self._send(
                    200,
                    json.dumps(result, default=str).encode("utf-8"),
                    "application/json",
                )

            # -------------------------------------------------
            # NORMAL SINGLE-FILE MODE
            # -------------------------------------------------

            has_file = False

            file_kind = ""

            if uploaded_files:
                filename, data = uploaded_files[0]

                os.makedirs(UPLOADS, exist_ok=True)

                safe_name = os.path.basename(filename)

                path = os.path.join(UPLOADS, safe_name)

                with open(path, "wb") as fh:
                    fh.write(data)

                has_file = True

                file_kind = kind_of(filename)

                task = f"{task}\n\n[Attached file saved at: {path}]"

            result = agent.run(task, has_file, file_kind)

            return self._send(
                200, json.dumps(result, default=str).encode("utf-8"), "application/json"
            )

        except Exception as exc:
            traceback.print_exc()

            try:
                r = route("", False, "")

                model = r.model

            except Exception:
                model = "Local Agent"

            result = {
                "answer": f"Server error: {exc}",
                "model": model,
                "reason": "Server-side exception.",
                "trace": [],
            }

            return self._send(
                500, json.dumps(result, default=str).encode("utf-8"), "application/json"
            )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    print(f"Workbench on http://localhost:{PORT}  (bound to loopback only)")

    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
