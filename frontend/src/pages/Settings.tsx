import { useEffect, useState } from "react";
import { Bell, CheckCircle2, Globe2, LockKeyhole, Save, Settings2, ShieldCheck, UserRound, Camera, Trash2 } from "lucide-react";
import { api } from "../services/api";
import type { Me } from "../types/api";

export function Settings() {
  const [me, setMe] = useState<Me | null>(null);
  const [saved, setSaved] = useState(false);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [avatarError, setAvatarError] = useState("");

  useEffect(() => {
    api.me().then(setMe).catch(() => {});
  }, []);

  const u = me?.user;

  return (
    <div className="page settings-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">ACCOUNT CENTER</p>
          <h1>Profil va sozlamalar</h1>
          <p>Akkaunt, interfeys va xavfsizlik parametrlarini boshqaring.</p>
        </div>
        <button
          className="btn primary"
          onClick={() => {
            setSaved(true);
            setTimeout(() => setSaved(false), 2200);
          }}
        >
          <Save size={14} /> Saqlash
        </button>
      </header>

      {saved && (
        <div className="notice info">
          <CheckCircle2 size={15} /> Sozlamalar muvaffaqiyatli saqlandi.
        </div>
      )}

      <div className="settings-grid">
        <section className="panel profile-card">
          <div className="settings-section-head">
            <div className="settings-icon">
              <UserRound size={17} />
            </div>
            <div>
              <h2>Profil ma’lumotlari</h2>
              <p>Joriy akkaunt va kompaniya konteksti.</p>
            </div>
          </div>

          <div className="profile-summary">
            <div className="profile-avatar-wrap">
              <div className="profile-avatar">
                {u?.avatar_url ? (
                  <img src={u.avatar_url} alt="Profil avatar" />
                ) : (
                  (u?.full_name || u?.username || "U").slice(0, 1).toUpperCase()
                )}
              </div>
              <label className="avatar-upload-btn" title="Avatarni almashtirish">
                <Camera size={13} />
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setAvatarError("");
                    setAvatarBusy(true);
                    try {
                      const r = await api.uploadAvatar(file);
                      setMe((m) =>
                        m ? { ...m, user: m.user ? { ...m.user, avatar_url: r.avatar_url } : m.user } : m
                      );
                      window.dispatchEvent(new CustomEvent("avtopark:avatar", { detail: { avatar_url: r.avatar_url } }));
                    } catch (err) {
                      setAvatarError(err instanceof Error ? err.message : "Avatar yuklanmadi");
                    } finally {
                      setAvatarBusy(false);
                      e.currentTarget.value = "";
                    }
                  }}
                />
              </label>
            </div>

            <div>
              <strong>{u?.full_name || u?.username || "Foydalanuvchi"}</strong>
              <span>{u?.role || "Foydalanuvchi"}</span>
              <small className="profile-avatar-hint">JPG, PNG yoki WEBP · 5 MB gacha</small>
            </div>

            {u?.avatar_url && (
              <button
                className="btn sm danger-ghost"
                disabled={avatarBusy}
                onClick={async () => {
                  setAvatarError("");
                  setAvatarBusy(true);
                  try {
                    await api.removeAvatar();
                    setMe((m) =>
                      m ? { ...m, user: m.user ? { ...m.user, avatar_url: null } : m.user } : m
                    );
                    window.dispatchEvent(new CustomEvent("avtopark:avatar", { detail: { avatar_url: null } }));
                  } catch (err) {
                    setAvatarError(err instanceof Error ? err.message : "Avatar o‘chirilmadi");
                  } finally {
                    setAvatarBusy(false);
                  }
                }}
              >
                <Trash2 size={13} /> Olib tashlash
              </button>
            )}
          </div>

          {avatarError && <div className="notice error avatar-error">{avatarError}</div>}

          <div className="settings-fields">
            <label>
              F.I.Sh.
              <input value={u?.full_name || ""} readOnly />
            </label>
            <label>
              Login
              <input value={u?.username || ""} readOnly />
            </label>
            <label>
              Rol
              <input value={u?.role || ""} readOnly />
            </label>
            <label>
              Kompaniya
              <input value={me?.company?.name || ""} readOnly />
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="settings-section-head">
            <div className="settings-icon">
              <ShieldCheck size={17} />
            </div>
            <div>
              <h2>Xavfsizlik</h2>
              <p>Akkaunt himoyasi va sessiya nazorati.</p>
            </div>
          </div>
          <div className="setting-row">
            <span>
              <LockKeyhole size={15} />
              <span>
                <b>Parol</b>
                <small>Parolingizni muntazam yangilang.</small>
              </span>
            </span>
            <button className="btn sm">O‘zgartirish</button>
          </div>
          <div className="setting-row">
            <span>
              <ShieldCheck size={15} />
              <span>
                <b>RBAC nazorati</b>
                <small>Rol va ruxsatlar server tomonda tekshiriladi.</small>
              </span>
            </span>
            <span className="badge ok">ACTIVE</span>
          </div>
        </section>

        <section className="panel">
          <div className="settings-section-head">
            <div className="settings-icon">
              <Settings2 size={17} />
            </div>
            <div>
              <h2>Interfeys</h2>
              <p>AVTOPARK PRO ko‘rinishi va til parametrlari.</p>
            </div>
          </div>
          <div className="setting-row">
            <span>
              <Globe2 size={15} />
              <span>
                <b>Til</b>
                <small>O‘zbekcha / Русский</small>
              </span>
            </span>
            <select defaultValue="uz">
              <option value="uz">O‘zbekcha</option>
              <option value="ru">Русский</option>
            </select>
          </div>
          <div className="setting-row">
            <span>
              <Bell size={15} />
              <span>
                <b>Bildirishnomalar</b>
                <small>Operatsion va xavfsizlik xabarlari.</small>
              </span>
            </span>
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <i />
            </label>
          </div>
        </section>
      </div>
    </div>
  );
}