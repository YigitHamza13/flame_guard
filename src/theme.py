"""Environment atmosphere; semantic evidence colours remain owned by plain/risk."""
import html
import json
import streamlit as st
from src.i18n import t

THEMES = {
 'ISS': {'class':'fg-env-iss','--bg':'#080d16','--surface':'#101a29','--line':'#526984','--text':'#f3f6fb','--muted':'#bbc9db','--accent':'#b4d9ff','--glow':'#152b42','texture':None},
 'Moon Base': {'class':'fg-env-moon','--bg':'#15171c','--surface':'#24282f','--line':'#677485','--text':'#f4f6fa','--muted':'#c3ccd7','--accent':'#d4e5fa','--glow':'#303945','texture':'moon'},
 'Mars Mission': {'class':'fg-env-mars','--bg':'#1c1210','--surface':'#30231f','--line':'#896b5c','--text':'#fff5ed','--muted':'#dec6b8','--accent':'#ffb68c','--glow':'#492b20','texture':'mars'},
 'Earth Lab': {'class':'fg-env-earth','--bg':'#101a20','--surface':'#1b2a32','--line':'#52747f','--text':'#f0fafb','--muted':'#b9d1d7','--accent':'#a4e5df','--glow':'#23423f','texture':'earth'},
}

def theme_css(env):
    theme=THEMES.get(env,THEMES['ISS'])
    scope='.stApp.'+theme['class']
    tokens=';'.join(f'{k}:{v}' for k,v in theme.items() if k.startswith('--'))
    texture=theme['texture']
    layer=(f"url('/app/static/images/{texture}.jpg')" if texture else
           'radial-gradient(circle at 12% 24%,#fff 0 1px,transparent 1.5px),radial-gradient(circle at 72% 54%,#fff 0 1px,transparent 1.5px)')
    if env == 'Earth Lab':
        layer = "linear-gradient(rgba(164,229,223,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(164,229,223,.35) 1px,transparent 1px)," + layer
    return f'''{scope}{{{tokens};background:var(--bg);color:var(--text);transition:background .9s ease,color .6s ease}}
{scope}::before{{content:"";position:fixed;inset:0;pointer-events:none;background-image:{layer};background-position:right top;background-size:{'40px 40px,40px 40px,55vw auto' if env=='Earth Lab' else '55vw auto'}; background-repeat:{'no-repeat' if texture else 'repeat'};opacity:.06;z-index:0}}
{scope} [data-testid="stMain"],{scope} [data-testid="stSidebar"]{{position:relative;z-index:1}}
{scope} [data-testid="stSidebar"]{{background:var(--surface);border-color:var(--line)}}
{scope} [data-testid="stSidebar"] [class*="st-key-nav_active_"] a{{background:var(--glow)!important;border-color:var(--accent);color:var(--text)}}
{scope} :is(input,textarea,[data-baseweb="select"]>div){{background:var(--surface);color:var(--text);border-color:var(--line)}}
{scope} :is(button,input,textarea,a):focus-visible{{outline-color:var(--accent)!important}}
{scope} [data-testid="stCaptionContainer"]{{opacity:1!important;color:var(--muted)!important}}
{scope} .hero-title{{border-bottom:2px solid var(--accent);padding-bottom:12px}}
{scope} .st-key-overview_actions button{{border-color:var(--accent);box-shadow:0 0 12px var(--glow)}}
{scope} .plain-card{{transition:opacity .4s ease}}
{scope}.fg-env-changing .plain-card{{animation:fg-card-reveal .4s ease}}
{scope} [data-testid="stTextInput"]:focus-within{{outline:1px solid var(--accent);border-radius:6px}}
.stApp.fg-env-iss .st-key-mission_toolbar{{border-radius:0 0 50% 5%;border-bottom:1px solid var(--accent)}}
@keyframes fg-card-reveal{{from{{opacity:.55}}to{{opacity:1}}}}
{scope} .fg-answer{{border-left-color:var(--accent)!important;background:var(--surface)!important}}
{scope} .fg-env-strip{{padding:10px 14px;border-left:3px solid var(--accent);background:var(--surface);color:var(--muted);font-size:14px;line-height:1.6}}
{scope} .wish.fg-env-relevant{{border-color:var(--accent);box-shadow:inset 3px 0 var(--accent)}}
{scope} .fg-env-badge{{display:inline-block;margin:6px 8px;padding:3px 8px;border:1px solid var(--accent);border-radius:4px;color:var(--text);background:var(--surface);font-size:13px}}
.stApp.fg-env-iss .tw-row>:nth-child(2),.stApp.fg-env-moon .tw-row>:nth-child(3){{outline:1px solid var(--accent);outline-offset:-1px}}
{scope}.fg-mood-high{{background:radial-gradient(1400px 700px at 70% -12%,rgba(232,96,64,.15),transparent 70%),var(--bg)!important}}
{scope}.fg-mood-medium{{background:radial-gradient(1400px 700px at 70% -12%,rgba(232,150,64,.12),transparent 65%),var(--bg)!important}}
{scope}.fg-mood-high [data-testid="stSidebar"]{{background:linear-gradient(rgba(232,96,64,.07),transparent),var(--surface)!important}}
{scope}.fg-env-changing::after{{content:"";position:fixed;inset:0;pointer-events:none;z-index:2;background:linear-gradient(transparent,var(--glow),transparent);animation:fg-env-sweep .9s ease both}}
@keyframes fg-env-sweep{{0%{{opacity:0;transform:translateY(-75%)}}50%{{opacity:.25}}100%{{opacity:0;transform:translateY(75%)}}}}
@media(prefers-reduced-motion:reduce){{{scope},{scope} *,{scope}::after{{animation:none!important;transition:none!important}}}}
'''

def theme_script(env):
    cls=THEMES.get(env,THEMES['ISS'])['class']
    return """<script>try{const a=window.parent.document.querySelector('.stApp');const next="""+json.dumps(cls)+""";
if(a&&!a.classList.contains(next)){for(const c of [...a.classList])if(c.startsWith('fg-env-'))a.classList.remove(c);
a.classList.add(next);if(!window.parent.matchMedia('(prefers-reduced-motion: reduce)').matches){a.classList.add('fg-env-changing');setTimeout(()=>a.classList.remove('fg-env-changing'),950);}}}catch(e){}</script>"""

def environment_strip(env):
    from src.plain import DEFAULT_ASSUMPTIONS
    if env=='Mars Mission':
        return t('Mars · mission phase and gravity unspecified · no measured Mars result in this collection')
    if env=='Moon Base':
        d=DEFAULT_ASSUMPTIONS[env]
        return t('Moon · partial gravity · default atmosphere from the FM² plan: {o2}% O₂, {pressure} kPa (poster 20240015307, PDF 1)',o2=f"{d['oxygen']:g}",pressure=f"{d['pressure']:g}")
    if env=='Earth Lab':
        d=DEFAULT_ASSUMPTIONS[env]
        return t('Earth laboratory · normal gravity · default air: {o2}% O₂, {pressure} kPa',o2=f"{d['oxygen']:g}",pressure=f"{d['pressure']:.1f}")
    return t('ISS · microgravity · environment colours are visual context, not a safety rating')

def apply_theme(env):
    st.markdown('<style>'+theme_css(env)+'</style>',unsafe_allow_html=True)
    st.html(theme_script(env),unsafe_allow_javascript=True)
    # Environment details are available in the selector; keep the planet area uncluttered.

def gravity_badge(record, env):
    known='microgravity' in str(record.get('project_type','')).lower()
    if not known or env=='Mars Mission': return t('Gravity comparison unavailable')
    return t('Same gravity class as the selected environment') if env=='ISS' else t('Different gravity class')
