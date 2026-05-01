import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

const INITIAL_SCHEDULE = {
  'ראשון': { active: false, start: '08:00', end: '21:00' },
  'שני': { active: false, start: '08:00', end: '21:00' },
  'שלישי': { active: false, start: '08:00', end: '21:00' },
  'רביעי': { active: false, start: '08:00', end: '21:00' },
  'חמישי': { active: false, start: '08:00', end: '21:00' },
  'שישי': { active: false, start: '08:00', end: '13:00' },
};

export default function Profile() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [degree, setDegree] = useState('מדעי המחשב');
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [selectedJobRole, setSelectedJobRole] = useState<number | null>(null);
  const [schedule, setSchedule] = useState(INITIAL_SCHEDULE);
  const [metadata, setMetadata] = useState<{tracks: any[], job_roles: any[]}>({ tracks: [], job_roles: [] });

  useEffect(() => {
    if (!user) return;

    Promise.all([api.getMetadata(), api.getProfile(user.user_id)])
      .then(([metaRes, profileRes]) => {
        setMetadata(metaRes.data);
        const p = profileRes.data;
        
        setDegree(p.degree || 'מדעי המחשב');
        setYearOfStudy(p.year_of_study || 1);
        
        if (p.interested_tracks?.length > 0) {
          setSelectedTrack(p.interested_tracks[0].id);
        }
        if (p.interested_job_roles?.length > 0) {
          setSelectedJobRole(p.interested_job_roles[0].id);
        }

        if (p.available_days) {
          const newSchedule = { ...INITIAL_SCHEDULE };
          const daysArray = p.available_days.split(', ');
          
          daysArray.forEach((dayStr: string) => {
            const match = dayStr.match(/(.+) \((.+)-(.+)\)/);
            if (match) {
              const [_, dayName, start, end] = match;
              if (newSchedule[dayName as keyof typeof INITIAL_SCHEDULE]) {
                newSchedule[dayName as keyof typeof INITIAL_SCHEDULE] = {
                  active: true,
                  start,
                  end
                };
              }
            }
          });
          setSchedule(newSchedule);
        }
      })
      .catch(err => console.error("Error loading profile:", err))
      .finally(() => setLoading(false));
  }, [user]);

  const calculateTotalWorkload = () => {
    let totalHours = 0;
    Object.values(schedule).forEach(day => {
      if (day.active) {
        const [startH, startM] = day.start.split(':').map(Number);
        const [endH, endM] = day.end.split(':').map(Number);
        const hours = endH - startH + (endM - startM) / 60;
        if (hours > 0) totalHours += hours;
      }
    });
    return Math.round(totalHours);
  };

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    
    try {
      const activeScheduleDays = Object.entries(schedule)
        .filter(([_, data]) => data.active)
        .map(([day, data]) => `${day} (${data.start}-${data.end})`);

      const profileData = {
        degree,
        year_of_study: yearOfStudy,
        available_days: activeScheduleDays.join(', '),
        target_workload: calculateTotalWorkload(),
        interested_track_ids: selectedTrack ? [selectedTrack] : [],
        interested_job_role_ids: selectedJobRole ? [selectedJobRole] : [],
        needs_flexible_attendance: false,
        onboarding_completed: true
      };

      await api.updateProfile(user.user_id, profileData);
      setIsEditing(false);
      navigate('/recommendations');
    } catch (err) {
      console.error("Update failed:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center mt-20 text-gray-800 text-xl" dir="rtl">טוען פרופיל...</div>;

  return (
    <div className="min-h-screen" dir="rtl">
      <div className="w-full max-w-6xl mx-auto px-8 py-8 bg-white shadow-lg rounded-2xl my-8 relative">
        
        <div className="flex justify-between items-center mb-8 border-b border-gray-100 pb-6">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-l from-emerald-600 to-teal-600">הפרופיל האקדמי שלי</h1>
            <p className="text-gray-500 text-sm">ניהול העדפות ומטרות קריירה</p>
          </div>
          {!isEditing ? (
            <button onClick={() => setIsEditing(true)} className="bg-emerald-600 text-white px-6 py-2 rounded-xl font-bold hover:bg-emerald-500 transition-all shadow-lg shadow-emerald-200">
              ערוך פרופיל
            </button>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => setIsEditing(false)} className="bg-gray-100 text-gray-600 px-4 py-2 rounded-xl hover:bg-gray-200">ביטול</button>
              <button onClick={handleSave} disabled={saving} className="bg-emerald-600 text-white px-6 py-2 rounded-xl font-bold hover:bg-emerald-500 disabled:opacity-50 transition-all">
                {saving ? 'שומר...' : 'שמור שינויים'}
              </button>
            </div>
          )}
        </div>

        <div className={`space-y-12 ${!isEditing ? 'opacity-75 grayscale-[0.2] pointer-events-none' : ''}`}>
          
          <section className="grid sm:grid-cols-2 gap-8">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">מסלול הלימודים</label>
              <select 
                disabled={!isEditing}
                value={degree}
                onChange={e => setDegree(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl p-3 focus:ring-2 focus:ring-emerald-400 focus:outline-none text-gray-800"
              >
                <option value="מדעי המחשב">מדעי המחשב</option>
                <option value="הנדסת תוכנה">הנדסת תוכנה</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">שנת לימודים</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4].map(y => (
                  <button
                    key={y}
                    disabled={!isEditing}
                    onClick={() => setYearOfStudy(y)}
                    className={`flex-1 py-2 rounded-lg border-2 font-bold transition-all ${yearOfStudy === y ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-100 text-gray-400'}`}
                  >
                    שנה {y === 1 ? "א'" : y === 2 ? "ב'" : y === 3 ? "ג'" : "ד'"}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800">מטרות קריירה ואשכולות</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {metadata.job_roles.map((role: any) => (
                <label key={role.id} className={`cursor-pointer px-4 py-3 rounded-xl border-2 flex items-center gap-3 transition-all ${selectedJobRole === role.id ? 'border-emerald-500 bg-emerald-50' : 'border-gray-100 opacity-60'}`}>
                  <input type="radio" disabled={!isEditing} checked={selectedJobRole === role.id} onChange={() => setSelectedJobRole(role.id)} className="hidden" />
                  <span className="font-medium text-sm text-gray-800">{role.title}</span>
                </label>
              ))}
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-xl font-bold text-gray-800">אשכול לימודים (התמחות)</h2>
            <div className="grid sm:grid-cols-3 gap-3">
              {metadata.tracks.map((track: any) => (
                <label key={track.id} className={`cursor-pointer px-4 py-3 rounded-xl border-2 flex items-center gap-3 transition-all ${selectedTrack === track.id ? 'border-teal-500 bg-teal-50 text-teal-800' : 'border-gray-100 opacity-60'}`}>
                  <input type="radio" disabled={!isEditing} checked={selectedTrack === track.id} onChange={() => setSelectedTrack(track.id)} className="hidden" />
                  <span className="font-medium text-xs">{track.name}</span>
                </label>
              ))}
            </div>
          </section>

          <section className="space-y-6 bg-gray-50 p-6 rounded-2xl">
            <h2 className="text-xl font-bold text-gray-800">זמני למידה פנויים</h2>
            <div className="grid gap-3">
              {Object.entries(schedule).map(([day, data]) => (
                <div key={day} className={`flex items-center gap-4 p-3 rounded-xl border bg-white ${data.active ? 'border-emerald-200 shadow-sm' : 'border-transparent opacity-60'}`}>
                  <label className="flex items-center gap-3 cursor-pointer w-24">
                    <input type="checkbox" disabled={!isEditing} checked={data.active} onChange={(e) => setSchedule({...schedule, [day]: {...data, active: e.target.checked}})} className="w-5 h-5 accent-emerald-500" />
                    <span className="font-bold text-gray-800">{day}</span>
                  </label>
                  {data.active && (
                    <div className="flex gap-2 items-center text-sm mr-auto" dir="ltr">
                      <input type="time" disabled={!isEditing} value={data.start} onChange={(e) => setSchedule({...schedule, [day]: {...data, start: e.target.value}})} className="border rounded p-1" />
                      <span className="text-gray-400">-</span>
                      <input type="time" disabled={!isEditing} value={data.end} onChange={(e) => setSchedule({...schedule, [day]: {...data, end: e.target.value}})} className="border rounded p-1" />
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="text-center font-bold text-emerald-700 bg-emerald-50 p-3 rounded-xl border border-emerald-100">
              סה"כ שעות שבועיות פנויות: {calculateTotalWorkload()}
            </div>
          </section>

          {!isEditing && (
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl text-blue-800 text-sm text-center font-medium">
              שינוי הפרטים והזמנים ישפיע באופן מיידי על דירוג הקורסים המומלצים עבורך.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}