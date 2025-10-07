## Blog App (Django + React Native)

### Backend
- Python venv: `venv\Scripts\activate` (if not already active)
- Configure environment: copy `.env.example` to `.env` and fill secrets
- Run DB migrations:
  - `venv\Scripts\python.exe manage.py migrate`
- Start server:
  - `venv\Scripts\python.exe manage.py runserver`

### API Highlights
- JWT auth: `/api/accounts/login/`, `/api/accounts/token/refresh/`
- Register + OTP: `/api/accounts/register/`, `/api/accounts/otp/send/`, `/api/accounts/otp/verify/`
- Stripe: `/api/accounts/stripe/create-intent/`, `/api/accounts/stripe/confirm/`
- Articles: `/api/articles/items/`, `/api/articles/categories/`
- Comments: `/api/comments/`

### Frontend (Expo React Native)
- From `rn_app`:
  - Install deps: `npm i`
  - Web (quick start): `npm run web`
  - Android emulator: `npm run android`

Notes
- React Native API base is set to Android emulator (`http://10.0.2.2:8000/api`) in `rn_app/src/api/client.js`. Change if running device/web (`http://localhost:8000/api`).
- Set Stripe and Twilio credentials in `.env` to enable payment and OTP.
- Article submission requires successful Stripe confirmation.

