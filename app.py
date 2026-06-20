"""
app.py — DevScan AI main interface.
Run: streamlit run app.py
"""
import streamlit as st
import os
import uuid
from dotenv import load_dotenv

load_dotenv(override=True)

from github_reader import get_repo_info, get_repo_files, download_file, parse_github_url
from sast_scanner import run_bandit_scan, check_common_ai_mistakes, get_security_score, calculate_deterministic_quality_score
from ai_reviewer import analyze_file, OLLAMA_MODEL, check_ollama_running, reset_ollama_cache
from security import sanitize_github_url, sanitize_api_key, sanitize_code_for_ai, generate_request_id, rate_limit_check
from compliance import check_compliance
from analytics import load_analytics, save_scan_result, calculate_roi

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="DevScan AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== SESSION ID for rate limiting =====
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# ===== STYLING =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --black-pearl: #1E2D3D;
    --prussian-blue: #003153;
    --pelorous: #48A9A6;
    --summer-sky: #38B6FF;
    --shimmer: #F6D860;
    --text-primary: #E8F4FD;
    --text-secondary: #A8C5DA;
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0A1628 0%, #003153 50%, #0A1628 100%);
    background-attachment: fixed;
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        radial-gradient(circle at 20% 20%, rgba(56,182,255,0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(72,169,166,0.08) 0%, transparent 50%);
    animation: bgPulse 8s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes bgPulse {
    0% { opacity: 0.5; transform: scale(1); }
    100% { opacity: 1; transform: scale(1.05); }
}

.hero-section {
    text-align: center;
    padding: 3rem 2rem 2rem;
    animation: heroFadeIn 1s ease-out forwards;
}

@keyframes heroFadeIn {
    from { opacity: 0; transform: translateY(-30px); }
    to   { opacity: 1; transform: translateY(0); }
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--summer-sky), var(--pelorous), var(--shimmer));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 1rem;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto 2rem;
    line-height: 1.7;
}

.badge-row {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 2.5rem;
}

.badge {
    background: rgba(56,182,255,0.1);
    border: 1px solid rgba(56,182,255,0.3);
    border-radius: 50px;
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    color: var(--summer-sky);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.badge:hover {
    background: rgba(56,182,255,0.2);
    border-color: var(--summer-sky);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(56,182,255,0.3);
}

.privacy-box {
    background: rgba(72,169,166,0.08);
    border: 1px solid rgba(72,169,166,0.3);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.gemini-warning {
    background: rgba(246,216,96,0.08);
    border: 1px solid rgba(246,216,96,0.4);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0;
    color: #F6D860;
    font-size: 0.9rem;
}

[data-testid="stTextInput"] input {
    background: rgba(0,49,83,0.6) !important;
    border: 1px solid rgba(56,182,255,0.2) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.8rem 1rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: var(--summer-sky) !important;
    box-shadow: 0 0 0 3px rgba(56,182,255,0.15) !important;
    outline: none !important;
}

[data-testid="stButton"] button {
    background: linear-gradient(135deg, var(--prussian-blue), var(--pelorous)) !important;
    border: 1px solid var(--pelorous) !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stButton"] button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 30px rgba(72,169,166,0.4) !important;
}

[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(72,169,166,0.2) !important;
    border-radius: 16px !important;
    margin-bottom: 1rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(72,169,166,0.15) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--summer-sky) !important;
    border-bottom: 2px solid var(--summer-sky) !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--black-pearl); }
::-webkit-scrollbar-thumb { background: var(--pelorous); border-radius: 10px; }
</style>

<div class="hero-section">
    <div class="hero-title">🔍 DevScan AI</div>
    <div class="hero-subtitle">
        AI-powered code review that runs entirely on your machine.
        Detect bugs, security vulnerabilities, and AI-generated mistakes
        before they reach production.
    </div>
    <div class="badge-row">
        <span class="badge">🖥️ Runs Locally</span>
        <span class="badge">🔒 100% Private</span>
        <span class="badge">⚡ SAST + AI</span>
        <span class="badge">🤖 AI-Code Detector</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ===== SIDEBAR — Gemini opt-in + model status =====
with st.sidebar:
    st.title("⚙️ Settings")
    st.divider()
    st.divider()
    # Ollama status
    ollama_online = check_ollama_running()
    if ollama_online:
        st.success(f"✅ Ollama Online")
        st.caption(f"Model: `{OLLAMA_MODEL}`")
    else:
        st.error("⚠️ Ollama Offline")
        st.caption(f"Expected model: `{OLLAMA_MODEL}`")
        st.caption("Run `ollama serve` in terminal to start it.")

    st.divider()

    # Gemini opt-in — explicit, with clear warning
    st.subheader("☁️ Gemini Backup")
    use_gemini = st.toggle(
        "Enable Gemini as backup",
        value=False,
        help="Only activates if Ollama fails. Sends code to Google."
    )

    if use_gemini:
        st.markdown("""
        <div class="gemini-warning">
        ⚠️ <strong>Cloud Review Active</strong><br>
        If Ollama is offline, your code will be sent to Google's servers for review.
        Only enable this if you accept that trade-off.
        </div>
        """, unsafe_allow_html=True)

        gemini_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            help="Get free at: aistudio.google.com"
        )
        if gemini_key_input:
            clean_key, err = sanitize_api_key(gemini_key_input, "Gemini")
            if clean_key:
                os.environ["GEMINI_API_KEY"] = clean_key
                st.success("Key saved for this session")
            elif err:
                st.error(err)
    else:
        st.caption("Gemini is off. Code stays on your machine.")

    st.divider()
    st.caption("v1.1 · Privacy-first code review")


# ===== TABS =====
tab_scan, tab_analytics = st.tabs(["🔍 Scan Repository", "📊 ROI Dashboard"])


# ===== ANALYTICS TAB =====
with tab_analytics:
    st.subheader("💰 Cost Savings & ROI Dashboard")
    data = load_analytics()
    roi  = calculate_roi(data)

    if data["total_scans"] == 0:
        st.info("No scans yet. Run your first scan to start tracking savings.")
    else:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("💵 API Costs Saved",    f"${roi['api_cost_saved']}")
        r2.metric("☁️ Cloud Tool Savings", f"${roi['coderabbit_cost_saved']}")
        r3.metric("⏰ Dev Hours Saved",    f"{roi['developer_hours_saved']} hrs")
        r4.metric("🛡️ Security Savings",  f"${roi['security_savings']}")
        st.success(f"💰 Total Estimated Savings: **${roi['total_saved_usd']}**")

        st.divider()
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total Scans",       data["total_scans"])
        d2.metric("Files Analyzed",    data["total_files_analyzed"])
        d3.metric("Bugs Found",        data["total_bugs_found"])
        d4.metric("Security Issues",   data["total_security_issues"])

        if data["scans_history"]:
            st.subheader("Recent Scans")
            for scan in reversed(data["scans_history"][-10:]):
                st.write(f"📁 **{scan['repo']}** — {scan['date']} — {scan['files']} files — {scan['bugs']} bugs")


# ===== SCAN TAB =====
with tab_scan:

    # Privacy status banner
    if use_gemini:
        st.markdown("""
        <div class="gemini-warning">
        ⚠️ Gemini backup is ON — if Ollama is offline, code will be sent to Google.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="privacy-box">
        🔒 <strong>Full Privacy Mode</strong> — AI review runs locally via Ollama.
        Your code never leaves this machine.
        </div>
        """, unsafe_allow_html=True)

    st.subheader("📋 Repository Details")

    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repository-name"
    )

    max_files = st.slider("Maximum files to analyze", 1, 10, 3)

    st.subheader("📜 Compliance Guardrails (Optional)")
    st.write("Upload your company's coding standards. DevScan checks every file against YOUR rules.")
    compliance_file = st.file_uploader(
        "Upload coding standards (.txt or .md)",
        type=["txt", "md"],
        help="Example: 'All functions must have docstrings', 'No global variables'"
    )

    compliance_rules = ""
    if compliance_file:
        compliance_rules = compliance_file.read().decode("utf-8")
        st.success(f"✅ Loaded {len(compliance_rules.splitlines())} compliance rules")

    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("🔄 Recheck Ollama"):
            reset_ollama_cache()
            if check_ollama_running(force=True):
                st.success("✅ Ollama Online!")
            else:
                st.error("❌ Still offline")
    with col1:
            analyze_clicked = st.button("🚀 Start Analysis", type="primary", use_container_width=True)

    # ===== MAIN ANALYSIS =====
    if analyze_clicked:

        # Rate limit check
        if not rate_limit_check(st.session_state["session_id"], max_requests=20, window_seconds=3600):
            st.error("⏱ Rate limit reached (20 scans/hour). Please wait before scanning again.")
            st.stop()

        # URL validation
        clean_url, url_error = sanitize_github_url(repo_url)
        if url_error:
            st.error(f"❌ {url_error}")
            st.stop()

        owner, repo = parse_github_url(clean_url)
        if not owner or not repo:
            st.error("❌ Could not read that GitHub URL. Format: https://github.com/owner/repo")
            st.stop()

        request_id = generate_request_id()
        st.caption(f"Analysis ID: `{request_id}`")

        # Privacy reminder during scan
        if not use_gemini:
            st.info("🔒 Running locally — your code stays on this machine throughout the entire analysis.")
        else:
            st.warning("⚠️ Gemini backup is enabled — code may be sent to Google if Ollama is offline.")
        
        st.markdown("""
        <div style="background:rgba(56,182,255,0.06);border:1px solid rgba(56,182,255,0.25);
        border-radius:12px;padding:1rem 1.5rem;margin:0.5rem 0;">
        ⏱️ <strong>This takes 30–60 seconds per file.</strong><br>
        <span style="color:#A8C5DA;font-size:0.9rem;">
        Unlike cloud tools that send your code to external servers,
        DevScan runs a full AI model privately on this machine.
        Your code never leaves. That's the trade-off — and it's worth it.
        </span>
        </div>
        """, unsafe_allow_html=True)

        progress_text = st.empty()

        with st.spinner("🔍 Fetching repository info..."):
            try:
                repo_info = get_repo_info(owner, repo)
            except Exception as e:
                st.error(f"❌ {e}")
                st.stop()

            if not repo_info:
                st.error("❌ Repository not found or is private. Check the URL.")
                st.stop()

        st.success(f"✅ Found: **{repo_info['full_name']}**")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⭐ Stars",    repo_info.get("stargazers_count", 0))
        m2.metric("🍴 Forks",   repo_info.get("forks_count", 0))
        m3.metric("💻 Language", repo_info.get("language", "Multiple"))
        m4.metric("📁 Size",    f"{repo_info.get('size', 0)} KB")

        st.divider()

        with st.spinner("📂 Reading repository files..."):
            files = get_repo_files(owner, repo)

        if not files:
            st.warning("⚠️ No code files found in this repository.")
            st.stop()

        st.info(f"Found {len(files)} code files. Analyzing top {min(max_files, len(files))}...")

        all_sast_issues   = []
        all_ai_issues     = []
        total_quality     = 0
        analyzed_count    = 0
        file_results      = []

        progress = st.progress(0)

        for i, file in enumerate(files[:max_files]):
            progress_text.markdown(f"🔍 **Analyzing {i+1}/{min(max_files, len(files))}:** `{file['name']}`")
            progress.progress((i + 1) / min(max_files, len(files)))

            code_content = download_file(file.get("download_url", ""))
            if not code_content:
                continue

            safe_code = sanitize_code_for_ai(code_content)

            sast_issues       = run_bandit_scan(safe_code, file["name"])
            ai_code_issues    = check_common_ai_mistakes(safe_code)
            compliance_issues = check_compliance(safe_code, file["name"], compliance_rules)

            all_sast_issues.extend(sast_issues)
            all_ai_issues.extend(ai_code_issues)

            # AI review — passes use_gemini flag
            ai_review, ai_source = analyze_file(
                safe_code,
                file["name"],
                sast_issues + ai_code_issues,
                use_gemini=use_gemini
            )

            security_score = get_security_score(sast_issues, ai_code_issues)
            quality_score  = calculate_deterministic_quality_score(
                safe_code, file["name"], sast_issues, ai_code_issues
            )

            total_quality  += quality_score
            analyzed_count += 1

            file_results.append({
                "name":              file["name"],
                "quality_score":     quality_score,
                "security_score":    security_score,
                "sast_issues":       sast_issues,
                "ai_code_issues":    ai_code_issues,
                "compliance_issues": compliance_issues,
                "ai_review":         ai_review,
                "ai_source":         ai_source,
            })

        progress.empty()
        progress_text.empty()

        # ===== RESULTS =====
        st.subheader("📊 Analysis Results")
        file_results.sort(key=lambda x: x["security_score"])

        for result in file_results:
            icon = "✅" if result["security_score"] >= 80 else "⚠️" if result["security_score"] >= 50 else "🚨"

            with st.expander(
                f"{icon} {result['name']} — Quality: {result['quality_score']}/10 | Security: {result['security_score']}/100",
                expanded=(result["security_score"] < 70)
            ):
                tab1, tab2, tab3, tab4 = st.tabs([
                    "🤖 AI Review", "🔐 SAST Issues", "⚡ AI-Code Risks", "📜 Compliance"
                ])

                with tab1:
                    st.caption(f"Reviewed by: {result['ai_source']}")
                    if "Ollama offline" in result["ai_source"] or "SAST Only" in result["ai_source"]:
                        st.warning(result["ai_review"])
                    else:
                        st.markdown(result["ai_review"])

                with tab2:
                    if result["sast_issues"]:
                        for issue in result["sast_issues"]:
                            sev = issue.get("severity", "LOW")
                            color = "🔴" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
                            st.write(f"{color} **Line {issue.get('line','?')}:** {issue.get('issue','')}")
                    else:
                        st.success("✅ No SAST issues found")

                with tab3:
                    if result["ai_code_issues"]:
                        for issue in result["ai_code_issues"]:
                            sev = issue.get("severity", "LOW")
                            color = "🔴" if sev == "HIGH" else "🟡"
                            st.write(f"{color} **{issue.get('category','')}:** {issue.get('issue','')}")
                    else:
                        st.success("✅ No AI-generated code risks detected")

                with tab4:
                    if compliance_rules:
                        if result["compliance_issues"]:
                            for issue in result["compliance_issues"]:
                                st.write(f"⚠️ **Rule:** {issue['rule']}")
                                st.write(f"   {issue['issue']}")
                        else:
                            st.success("✅ All compliance rules passed")
                    else:
                        st.info("Upload a compliance file above to check your standards")

        # ===== SUMMARY =====
        if analyzed_count > 0:
            st.divider()
            st.subheader("📈 Overall Repository Summary")

            avg_quality  = total_quality / analyzed_count
            total_issues = len(all_sast_issues) + len(all_ai_issues)
            high_issues  = len([i for i in all_sast_issues + all_ai_issues if i.get("severity") == "HIGH"])

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Files Analyzed",    analyzed_count)
            s2.metric("Avg Quality Score", f"{avg_quality:.1f}/10")
            s3.metric("Total Issues",      total_issues)
            s4.metric("🚨 High Severity",  high_issues)

            if avg_quality >= 8 and high_issues == 0:
                st.success("✅ VERDICT: Production Ready")
            elif avg_quality >= 6 and high_issues <= 2:
                st.warning("⚠️ VERDICT: Needs Minor Fixes")
            elif avg_quality >= 4:
                st.error("🚨 VERDICT: Needs Major Fixes")
            else:
                st.error("🛑 VERDICT: Do Not Deploy")

            save_scan_result(
                repo_name=f"{owner}/{repo}",
                files_analyzed=analyzed_count,
                bugs_found=sum(len(r["sast_issues"]) for r in file_results),
                security_issues=sum(1 for r in file_results for i in r["sast_issues"] if i.get("severity") == "HIGH"),
                ai_risks=sum(len(r["ai_code_issues"]) for r in file_results)
            )

# ===== FOOTER =====
st.divider()
st.caption("DevScan AI • Local AI-Powered Code Review • Your code stays private")