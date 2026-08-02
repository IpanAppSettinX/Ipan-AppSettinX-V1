# Firebase Authentication

Login desktop memakai Firebase Email/Password. Password dikirim langsung dari
proses Python ke Firebase Identity Toolkit dan tidak disimpan atau dicatat.
Setelah token diterbitkan, Python mengikat akun ke perangkat lewat Firestore
Security Rules: satu akun hanya memiliki satu hash perangkat, dan satu hash
perangkat hanya dimiliki satu akun. Pasangan binding ditulis dalam satu
`commit` atomik; aturan memeriksa silang kedua dokumen dengan `getAfter()`
sehingga client tidak bisa menulis setengah pasangan atau data yang
tidak konsisten. `MachineGuid` mentah tidak pernah keluar dari proses;
aplikasi mengirim SHA-256 yang di-scope ke project.

Seluruh fitur ini berjalan di paket Firebase **Spark (gratis)** — tidak perlu
Cloud Functions, tidak perlu mendaftarkan metode pembayaran.

## Setup admin

1. Di Firebase Console, aktifkan Authentication > Sign-in method > Email/Password.
2. Aktifkan Firestore pada project `ipan-app-settinx`.
3. Instal Firebase CLI dan login: `npm install -g firebase-tools`, lalu `firebase login`.
4. Deploy aturan keamanan: `firebase deploy --only firestore:rules`.
5. Jalankan aplikasi:

```powershell
$env:PYTHONPATH = "src"
python -m ipan_optimizer.main
```

Tidak ada environment variable tambahan yang diperlukan; konfigurasi project
sudah tertanam di `src/ipan_optimizer/app/auth.py`.

## Reset HWID

Akun pelanggan dibuat melalui Firebase Console. Reset HWID dilakukan admin
dengan menghapus dokumen UID dari `deviceUsers` **dan** dokumen hash
pasangannya dari `deviceBindings` lewat Firebase Console (kedua penghapusan
tidak harus atomik karena client selalu menulis ulang pasangan lengkap).
Client tidak memiliki izin update/delete pada koleksi tersebut.

## Catatan keamanan

Firebase Web API key bukan secret. Keamanan berasal dari Firebase Auth,
validasi ID token oleh Firestore, aturan `firestore.rules` yang menolak
tulis yang bentrok, dan pembatasan API key di Google Cloud Console. Bila
aturan belum di-deploy atau menolak permintaan, aplikasi gagal-tertutup
(fail-closed) dan login ditolak.
