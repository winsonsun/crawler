# -*- coding: utf-8 -*-

def get_age_gate_bypass_js():
    """Returns a robust, multi-lingual JS script to bypass age gates and Cloudflare challenges."""
    return '''
        return (async () => {
            const delay = (ms) => new Promise(r => setTimeout(r, ms));
            
            // 1. Handle Age Gates (Multilingual: ZH, JA, EN)
            const clickAgeGate = async () => {
                // Find checkbox
                const ageCheck = document.querySelector('input[type="checkbox"]');
                if (ageCheck && !ageCheck.checked) {
                    console.log("Checking age box...");
                    ageCheck.click();
                    await delay(500); // Wait for state to register
                }
                
                // Find button
                const btns = Array.from(document.querySelectorAll('button, a, .button, .btn'));
                const btn = btns.find(b => {
                    const t = b.innerText.toLowerCase();
                    return t.includes('成年') || 
                           t.includes('確認') || 
                           t.includes('18歳以上') || 
                           t.includes('enter') || 
                           t.includes('confirm') ||
                           t.includes('i am 18') ||
                           t.includes('agree');
                });
                
                if (btn) {
                    console.log("Clicking confirm button...");
                    btn.click();
                    return true;
                }
                return false;
            };

            await clickAgeGate();
            await delay(2000); // Wait for navigation/refresh

            // 2. Handle Cloudflare / Just a moment
            let attempts = 0;
            while ((document.title.includes("Just a moment") || document.body.innerText.includes("Just a moment")) && attempts < 10) {
                await delay(2000);
                attempts++;
            }
            
            return { 
                cookie: document.cookie, 
                userAgent: navigator.userAgent,
                title: document.title
            };
        })();
    '''
