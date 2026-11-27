# Setup guide (all free)

Do these in order. Each step gives you values to paste into Render in step 4.
Never paste keys into chat or commit them to GitHub.

## 1. Supabase (the recipe book database)
1. Sign up at https://supabase.com → **New project** (any name, e.g. `recipebot`, region: closest to Israel, e.g. Frankfurt).
2. Open **SQL Editor**, paste the contents of [`supabase/schema.sql`](supabase/schema.sql), click **Run**.
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role** key (secret) → `SUPABASE_SERVICE_KEY`

## 2. Gemini
You already have it → `GEMINI_API_KEY`.

## 3. WhatsApp (Meta for Developers, free test number)
1. Go to https://developers.facebook.com → **My Apps → Create App** → use case **Other** → type **Business**.
2. In the app, add the **WhatsApp** product. Meta creates a free **test phone number** for you.
3. In **WhatsApp → API Setup**:
   - Copy **Phone number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - Under **To**, add Michal's number (and yours) and confirm the code each phone receives. Only these numbers can talk to the bot.
4. In **App settings → Basic**, copy **App secret** → `WHATSAPP_APP_SECRET`.
5. Permanent token (the one on the API Setup page expires after 24 hours):
   **Business settings → Users → System users → Add** (role Admin) → **Add assets** → your app (full control)
   → **Generate token** → pick the app, expiry **Never**, permissions `whatsapp_business_messaging` and `whatsapp_business_management`
   → copy → `WHATSAPP_TOKEN`.

## 4. Render (runs the bot)
1. Sign up at https://render.com with GitHub → **New → Blueprint** → pick the `RecipeBot` repo. It reads `render.yaml`.
2. Fill in the values from the steps above. `ALLOWED_NUMBERS` = Michal's and your numbers, comma-separated, like `972501234567,972521234567` (no `+`, no leading 0).
3. Deploy. Your bot URL looks like `https://recipebot-xxxx.onrender.com`. Open it; you should see `{"ok":true}`.
4. In Render → **Environment**, copy the generated `WHATSAPP_VERIFY_TOKEN`.

## 5. Connect WhatsApp to the bot
In Meta → **WhatsApp → Configuration → Webhook → Edit**:
- Callback URL: `https://recipebot-xxxx.onrender.com/webhook`
- Verify token: the `WHATSAPP_VERIFY_TOKEN` from Render
- Click **Verify and save**, then **Manage** → subscribe to **messages**.

## 6. Try it
Michal sends a reel link to the test number on WhatsApp. The first reply after a quiet period can take ~30 seconds while Render's free server wakes up.
