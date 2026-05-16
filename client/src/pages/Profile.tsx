import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

type ScheduleDay = keyof typeof INITIAL_SCHEDULE;

function parseScheduleFromProfile(profile: {
  availabilities?: { day_of_week: string; start_time: string; end_time: string }[];
  available_days?: string;
}) {
  const schedule = { ...INITIAL_SCHEDULE };

  if (profile.availabilities?.length) {
    profile.availabilities.forEach((a) => {
      const day = a.day_of_week as ScheduleDay;
      if (schedule[day]) {
        schedule[day] = { active: true, start: a.start_time, end: a.end_time };
      }
    });
    return schedule;
  }

  if (profile.available_days) {
    profile.available_days.split(', ').forEach((dayStr) => {
      const match = dayStr.match(/(.+) \((.+)-(.+)\)/);
      if (match) {
        const [, dayName, start, end] = match;
        const day = dayName as ScheduleDay;
        if (schedule[day]) {
          schedule[day] = { active: true, start, end };
        }
      }
    });
  }

  return schedule;
}

function yearLabel(y: number) {
  return y === 1 ? "א'" : y === 2 ? "ב'" : y === 3 ? "ג'" : "ד'";
}

export default function Profile() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  const [savedProfile, setSavedProfile] = useState<any>(null);
  const [metadata, setMetadata] = useState<{ tracks: any[]; job_roles: any[] }>({
    tracks: [],
    job_roles: [],
  });

  const [degree, setDegree] = useState('מדעי המחשב');
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);
  const [selectedJobRole, setSelectedJobRole] = useState<number | null>(null);
  const [schedule, setSchedule] = useState(INITIAL_SCHEDULE);

  const loadFormFromProfile = (p: any) => {
    setDegree(p.degree || 'מדעי המחשב');
    setYearOfStudy(p.year_of_study || 1);
    setSelectedTrack(p.interested_tracks?.length > 0 ? p.interested_tracks[0].id : null);
    setSelectedJobRole(p.interested_job_roles?.length > 0 ? p.interested_job_roles[0].id : null);
    setSchedule(parseScheduleFromProfile(p));
  };

  useEffect(() => {
    if (!user) return;

    Promise.all([api.getMetadata(), api.getProfile(user.user_id)])
      .then(([metaRes, profileRes]) => {
        setMetadata(metaRes.data);
        setSavedProfile(profileRes.data);
        loadFormFromProfile(profileRes.data);
      })
      .catch((err) => console.error('Error loading profile:', err))
      .finally(() => setLoading(false));
  }, [user]);

  const calculateTotalWorkload = () => {
    let totalHours = 0;
    Object.values(schedule).forEach((day) => {
      if (day.active && day.start && day.end) {
        const [startH, startM] = day.start.split(':').map(Number);
        const [endH, endM] = day.end.split(':').map(Number);
        const hours = endH - startH + (endM - startM) / 60;
        if (hours > 0) totalHours += hours;
      }
    });
    return Math.round(totalHours);
  };

  const handleCancel = () => {
    if (savedProfile) loadFormFromProfile(savedProfile);
    setSaveError('');
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    setSaveError('');

    try {
      const activeScheduleDays = Object.entries(schedule)
        .filter(([, data]) => data.active)
        .map(([day, data]) => `${day} (${data.start}-${data.end})`);

      const availabilities = Object.entries(schedule)
        .filter(([, data]) => data.active)
        .map(([day, data]) => ({
          day_of_week: day,
          start_time: data.start,
          end_time: data.end,
        }));

      const workload = calculateTotalWorkload();

      const res = await api.updateProfile(user.user_id, {
        degree,
        year_of_study: yearOfStudy,
        available_days: activeScheduleDays.join(', '),
        availabilities,
        target_workload: workload || 0,
        needs_flexible_attendance: savedProfile?.needs_flexible_attendance ?? false,
        interested_track_ids: selectedTrack ? [selectedTrack] : [],
        interested_job_role_ids: selectedJobRole ? [selectedJobRole] : [],
        onboarding_completed: true,
      });

      setSavedProfile(res.data);
      loadFormFromProfile(res.data);
      setIsEditing(false);
    } catch (err) {
      console.error('Update failed:', err);
      setSaveError('שגיאה בשמירת ההעדפות. אנא נסי שוב.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64" dir="rtl">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500" />
      </div>
    );
  }

  const displayProfile = savedProfile;
  const workloadDisplay = isEditing ? calculateTotalWorkload() : displayProfile?.target_workload || 0;

  return (
    <div className="space-y-8 animate-fade-in" dir="rtl">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-l from-emerald-500 to-teal-500">
            עריכת ההעדפות
          </h1>
          <p className="text-gray-500 mt-2">ניהול פרטים אקדמיים, מטרות קריירה וזמני למידה</p>
        </div>
        <div className="flex gap-2">
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-medium transition-all shadow-md shadow-emerald-500/20"
            >
              עריכת העדפות
            </button>
          ) : (
            <>
              <button
                onClick={handleCancel}
                className="text-gray-500 hover:text-gray-800 px-4 py-2.5 rounded-lg border border-gray-200 bg-white transition-colors"
              >
                ביטול
              </button>
              <button
                onClick={handleSave}
                disabled={saving || calculateTotalWorkload() <= 0}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-medium transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50"
              >
                {saving ? 'שומר...' : 'שמור שינויים'}
              </button>
            </>
          )}
        </div>
      </header>

      {/* Summary cards — same layout as Dashboard "ההעדפות שלך" */}
      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold mb-6">ההעדפות שלך</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">שנת לימודים</div>
            <div className="font-medium text-lg">שנה {yearLabel(isEditing ? yearOfStudy : displayProfile?.year_of_study || 1)}</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">תואר</div>
            <div className="font-medium text-lg truncate">
              {isEditing ? degree : displayProfile?.degree || 'מדעי המחשב'}
            </div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">עומס יעד</div>
            <div className="font-medium text-lg">{workloadDisplay} שעות/שבוע</div>
          </div>
          <div className="bg-gray-100 p-4 rounded-xl border border-gray-200">
            <div className="text-gray-400 text-xs mb-1 uppercase tracking-wider">מסלולים</div>
            <div className="font-medium text-sm line-clamp-2">
              {isEditing
                ? metadata.tracks.find((t) => t.id === selectedTrack)?.name || 'לא נבחר'
                : displayProfile?.interested_tracks?.length > 0
                  ? displayProfile.interested_tracks.map((t: any) => t.name).join(', ')
                  : 'לא נבחר'}
            </div>
          </div>
        </div>
      </div>

      <div className={`glass-panel p-6 md:p-8 space-y-10 ${!isEditing ? 'opacity-90' : ''}`}>
        {/* Degree */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">מסלול הלימודים</h2>
          <label className="block text-sm text-gray-600 font-medium">בחר/י את מסלול הלימודים</label>
          <select
            disabled={!isEditing}
            value={degree}
            onChange={(e) => setDegree(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-emerald-400 disabled:opacity-70"
          >
            <option value="מדעי המחשב">מדעי המחשב</option>
            <option value="הנדסת תוכנה">הנדסת תוכנה</option>
          </select>
        </section>

        {/* Year */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">שנת לימודים</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((y) => (
              <button
                key={y}
                type="button"
                disabled={!isEditing}
                onClick={() => setYearOfStudy(y)}
                className={`p-6 text-center rounded-xl border-2 transition-all disabled:cursor-default ${
                  yearOfStudy === y
                    ? 'bg-emerald-50 border-emerald-500 shadow-md'
                    : 'bg-white border-gray-100 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl font-bold text-gray-800">שנה {yearLabel(y)}</div>
              </button>
            ))}
          </div>
        </section>

        {/* Career goals — Onboarding step 3 pattern */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">מטרות קריירה ומסלולים</h2>
          <p className="text-sm text-gray-500">
            ספר/י לנו לאן את/ה מכוון/ת בתעשייה כדי שנוכל להמליץ על הקורסים הרלוונטיים ביותר.
          </p>

          <div>
            <label className="block text-sm text-gray-700 mb-3 font-medium">תפקיד מבוקש בתעשייה</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {metadata.job_roles.map((role: any) => (
                <label
                  key={role.id}
                  className={`px-4 py-3 rounded-xl border text-sm font-medium transition-all flex items-center gap-3 ${
                    selectedJobRole === role.id
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm'
                      : 'bg-white border-gray-200 text-gray-600'
                  } ${isEditing ? 'cursor-pointer hover:bg-gray-50' : 'cursor-default opacity-80'}`}
                >
                  <input
                    type="radio"
                    name="jobRole"
                    disabled={!isEditing}
                    checked={selectedJobRole === role.id}
                    onChange={() => setSelectedJobRole(role.id)}
                    className="w-4 h-4 text-emerald-500 focus:ring-emerald-500"
                  />
                  {role.title}
                </label>
              ))}
            </div>
          </div>

          {metadata.tracks.length > 0 && (
            <div className="pt-4">
              <label className="block text-sm text-gray-700 mb-3 font-medium">אשכול לימודים (התמחות)</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {metadata.tracks.map((track: any) => (
                  <label
                    key={track.id}
                    className={`px-4 py-3 rounded-xl border text-sm font-medium transition-all flex items-center gap-3 ${
                      selectedTrack === track.id
                        ? 'bg-teal-50 border-teal-500 text-teal-800 shadow-sm'
                        : 'bg-white border-gray-200 text-gray-600'
                    } ${isEditing ? 'cursor-pointer hover:bg-gray-50' : 'cursor-default opacity-80'}`}
                  >
                    <input
                      type="radio"
                      name="track"
                      disabled={!isEditing}
                      checked={selectedTrack === track.id}
                      onChange={() => setSelectedTrack(track.id)}
                      className="w-4 h-4 text-teal-500 focus:ring-teal-500"
                    />
                    {track.name}
                  </label>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Schedule — Onboarding step 5 pattern */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">זמני למידה (מערכת שעות)</h2>
          <p className="text-sm text-gray-500">
            סמן/י באילו ימים ושעות את/ה פנוי/ה להגיע להרצאות או ללמוד בבית.
          </p>

          <div className="space-y-3">
            {Object.entries(schedule).map(([dayName, data]) => (
              <div
                key={dayName}
                className={`flex items-center gap-4 p-3 rounded-xl border transition-colors ${
                  data.active ? 'bg-emerald-50 border-emerald-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <label className={`flex items-center gap-3 w-28 ${isEditing ? 'cursor-pointer' : 'cursor-default'}`}>
                  <input
                    type="checkbox"
                    disabled={!isEditing}
                    checked={data.active}
                    onChange={(e) =>
                      setSchedule({
                        ...schedule,
                        [dayName]: { ...data, active: e.target.checked },
                      })
                    }
                    className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                  />
                  <span className={`font-medium ${data.active ? 'text-emerald-800' : 'text-gray-500'}`}>
                    יום {dayName}
                  </span>
                </label>
                <div
                  className={`flex items-center gap-2 flex-grow transition-opacity duration-200 ${
                    data.active ? 'opacity-100' : 'opacity-40 pointer-events-none'
                  }`}
                >
                  <span className="text-sm text-gray-500">מ-</span>
                  <input
                    type="time"
                    disabled={!isEditing}
                    value={data.start}
                    onChange={(e) =>
                      setSchedule({
                        ...schedule,
                        [dayName]: { ...data, start: e.target.value },
                      })
                    }
                    className="bg-white border border-gray-300 rounded-md p-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                  />
                  <span className="text-sm text-gray-500">עד-</span>
                  <input
                    type="time"
                    disabled={!isEditing}
                    value={data.end}
                    onChange={(e) =>
                      setSchedule({
                        ...schedule,
                        [dayName]: { ...data, end: e.target.value },
                      })
                    }
                    className="bg-white border border-gray-300 rounded-md p-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="bg-gray-100 p-4 rounded-xl flex justify-between items-center border border-gray-200">
            <span className="text-gray-600 font-medium">סך שעות למידה פנויות בשבוע:</span>
            <span className="text-2xl font-bold text-gray-800">
              {workloadDisplay} <span className="text-sm font-normal">שעות</span>
            </span>
          </div>
        </section>

        {saveError && (
          <p className="text-red-500 text-sm font-medium text-center">{saveError}</p>
        )}

        {!isEditing && (
          <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl text-blue-800 text-sm text-center font-medium">
            שינוי ההעדפות ישפיע באופן מיידי על דירוג הקורסים המומלצים עבורך.{' '}
            <Link to="/history" className="text-emerald-700 hover:underline font-semibold">
              לעריכת היסטוריית קורסים →
            </Link>
          </div>
        )}
      </div>

      {isEditing && (
        <div className="flex justify-end">
          <button
            onClick={() => navigate('/')}
            className="text-gray-500 hover:text-gray-800 text-sm"
          >
            חזרה ללוח הבקרה
          </button>
        </div>
      )}
    </div>
  );
}
