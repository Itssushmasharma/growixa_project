export interface TemplatePreset {
  id: string;
  name: string;
  category: string;
  subject: string;
  body_html: string;
  body_text: string;
}

export const TEMPLATE_PRESETS: TemplatePreset[] = [
  {
    id: "product-launch",
    name: "Growixa Product Launch",
    category: "Announcement",
    subject: "🚀 Introducing Growixa — Your Growth Engine is Here",
    body_html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Growixa Product Launch</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f8;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f4f8;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#a78bfa 100%);padding:48px 40px;text-align:center;">
              <p style="margin:0 0 16px;font-size:14px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.75);">We are live 🎉</p>
              <h1 style="margin:0 0 16px;font-size:38px;font-weight:800;color:#ffffff;line-height:1.2;letter-spacing:-1px;">Growixa is Here.</h1>
              <p style="margin:0;font-size:16px;color:rgba(255,255,255,0.85);line-height:1.6;max-width:420px;margin:0 auto;">The email marketing platform built for teams who care about growth — not just sends.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:40px 48px 24px;">
              <p style="margin:0 0 16px;font-size:16px;color:#374151;line-height:1.7;">Hi there 👋,</p>
              <p style="margin:0 0 16px;font-size:16px;color:#374151;line-height:1.7;">We've been building something we're incredibly proud of — and today, we're finally ready to share it with the world.</p>
              <p style="margin:0;font-size:16px;color:#374151;line-height:1.7;"><strong>Growixa</strong> is an all-in-one email marketing platform that helps you send smarter, automate faster, and grow bigger.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 48px 32px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td width="30%" style="background:#f5f3ff;border-radius:10px;padding:20px;text-align:center;vertical-align:top;">
                    <p style="font-size:28px;margin:0 0 8px;">📧</p>
                    <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#4f46e5;">Smart Campaigns</p>
                    <p style="margin:0;font-size:12px;color:#6b7280;line-height:1.5;">Create & schedule in minutes.</p>
                  </td>
                  <td width="5%"></td>
                  <td width="30%" style="background:#f0fdf4;border-radius:10px;padding:20px;text-align:center;vertical-align:top;">
                    <p style="font-size:28px;margin:0 0 8px;">⚡</p>
                    <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#16a34a;">Automations</p>
                    <p style="margin:0;font-size:12px;color:#6b7280;line-height:1.5;">Set it up once, run 24/7.</p>
                  </td>
                  <td width="5%"></td>
                  <td width="30%" style="background:#fff7ed;border-radius:10px;padding:20px;text-align:center;vertical-align:top;">
                    <p style="font-size:28px;margin:0 0 8px;">📊</p>
                    <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#ea580c;">Analytics</p>
                    <p style="margin:0;font-size:12px;color:#6b7280;line-height:1.5;">Real-time clicks & opens.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 48px 40px;text-align:center;">
              <a href="https://growixa.com/signup" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;padding:16px 40px;border-radius:8px;">Start Free Trial →</a>
            </td>
          </tr>
          <tr>
            <td style="background:#f9fafb;padding:24px 48px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">© 2026 Growixa, Inc. · <a href="#" style="color:#6366f1;text-decoration:none;">Unsubscribe</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`,
    body_text: `Hi there,\n\nWe are excited to announce that Growixa is officially live!\n\nGrowixa is an all-in-one email marketing platform — smart campaigns, automations, and real-time analytics.\n\nStart your free trial: https://growixa.com/signup\n\n© 2026 Growixa, Inc.`,
  },
  {
    id: "welcome-onboarding",
    name: "Customer Welcome Email",
    category: "Onboarding",
    subject: "Welcome to Growixa! Here's how to get started 👋",
    body_html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Welcome to Growixa</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
          <tr>
            <td style="padding:40px 40px 20px;text-align:left;">
              <h2 style="margin:0 0 8px;font-size:24px;color:#0f172a;">Welcome onboard! 🎉</h2>
              <p style="margin:0;font-size:15px;color:#475569;line-height:1.6;">We're thrilled to have you with us. Here are 3 quick steps to kickstart your first campaign with Growixa:</p>
            </td>
          </tr>
          <tr>
            <td style="padding:10px 40px 30px;">
              <div style="background:#f1f5f9;border-radius:8px;padding:16px;margin-bottom:12px;">
                <strong style="color:#0f172a;">1. Import your Contacts</strong>
                <p style="margin:4px 0 0;font-size:13px;color:#64748b;">Upload your CSV list or sync via API seamlessly.</p>
              </div>
              <div style="background:#f1f5f9;border-radius:8px;padding:16px;margin-bottom:12px;">
                <strong style="color:#0f172a;">2. Pick a Template</strong>
                <p style="margin:4px 0 0;font-size:13px;color:#64748b;">Choose from dozens of high-converting design layouts.</p>
              </div>
              <div style="background:#f1f5f9;border-radius:8px;padding:16px;">
                <strong style="color:#0f172a;">3. Send or Schedule</strong>
                <p style="margin:4px 0 0;font-size:13px;color:#64748b;">Schedule your broadcast or trigger automated workflows.</p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 40px 40px;text-align:left;">
              <a href="https://growixa.com/dashboard" style="display:inline-block;background:#4f46e5;color:#ffffff;text-decoration:none;font-size:14px;font-weight:600;padding:12px 24px;border-radius:6px;">Go to Dashboard →</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`,
    body_text: `Welcome onboard!\n\nHere are 3 quick steps to kickstart your first campaign with Growixa:\n1. Import your Contacts\n2. Pick a Template\n3. Send or Schedule\n\nGo to Dashboard: https://growixa.com/dashboard`,
  },
  {
    id: "monthly-newsletter",
    name: "Monthly Newsletter",
    category: "Newsletter",
    subject: "Growixa Digest: Top Marketing Trends & Product Updates",
    body_html: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Monthly Newsletter</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #cbd5e1;">
          <tr>
            <td style="background:#0f172a;padding:32px 40px;text-align:left;">
              <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#818cf8;letter-spacing:2px;text-transform:uppercase;">Monthly Edition</p>
              <h1 style="margin:0;font-size:28px;color:#ffffff;">The Growth Digest 📰</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 40px;">
              <h3 style="margin:0 0 10px;font-size:18px;color:#0f172a;">5 Strategies for High Email Deliverability</h3>
              <p style="margin:0 0 16px;font-size:14px;color:#475569;line-height:1.6;">Learn how top domain warming and DKIM configuration ensure your emails hit the primary inbox every time.</p>
              <a href="#" style="color:#4f46e5;font-weight:600;font-size:14px;text-decoration:none;">Read article →</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`,
    body_text: `The Growth Digest 📰\n\n5 Strategies for High Email Deliverability\nLearn how domain warming ensures inbox placement.\n\nRead article: https://growixa.com/blog`,
  },
];
