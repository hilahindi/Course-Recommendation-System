import { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  CourseStatBox,
  CourseModalCloseButton,
  courseModalOverlayClass,
  courseModalShellClass,
} from '../components/courseDetailUi';

interface Course {
  course_code: number;
  name: string;
  category?: string | null;
  workload: number;
  credits: number;
  mandatory_attendance?: boolean;
  skills?: { name: string }[] | string | null;
  prerequisites?: string;
}

interface AdminUser {
  id: number;
  name: string | null;
  email: string;
  role: string;
}

interface CourseFields {
  name: string;
  category: string;
  workload: number;
  credits: number;
  prerequisites: string;
  skills: string;
}

const EMPTY_CREATE = {
  course_code: '',
  name: '',
  category: 'elective',
  workload: 3,
  credits: 3,
  prerequisites: '',
  skills: '',
};

const inputClass =
  'w-full bg-gray-100 border border-gray-200 rounded-lg p-2 text-gray-800 focus:outline-none focus:border-emerald-400 transition-colors';
const labelClass = 'block text-xs font-medium text-gray-500 mb-1';

function skillsToString(skills: Course['skills']): string {
  if (Array.isArray(skills)) return skills.map((s) => s.name).join(', ');
  return skills || '';
}

export default function Admin() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [createForm, setCreateForm] = useState<typeof EMPTY_CREATE>(EMPTY_CREATE);
  const [editCourse, setEditCourse] = useState<Course | null>(null);
  const [editForm, setEditForm] = useState<CourseFields | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState('');

  const loadCourses = () =>
    api.getCourses({ force: true }).then((res) => setCourses(res.data as Course[]));
  const loadUsers = () =>
    api.adminListUsers().then((res) => setUsers(res.data as AdminUser[]));

  useEffect(() => {
    loadCourses().catch((e) => setError(String(e)));
    loadUsers().catch((e) => setError(String(e)));
  }, []);

  const openEdit = (c: Course) => {
    setError('');
    setEditCourse(c);
    setEditForm({
      name: c.name,
      category: c.category || 'elective',
      workload: c.workload ?? 3,
      credits: c.credits ?? 3,
      prerequisites: c.prerequisites || '',
      skills: skillsToString(c.skills),
    });
  };

  const closeEdit = () => {
    setEditCourse(null);
    setEditForm(null);
  };

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.adminCreateCourse({
        course_code: Number(createForm.course_code),
        name: createForm.name,
        category: createForm.category,
        workload: Number(createForm.workload),
        credits: Number(createForm.credits),
        prerequisites: createForm.prerequisites,
        skills: createForm.skills,
      });
      await loadCourses();
      setCreateForm(EMPTY_CREATE);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'הפעולה נכשלה');
    } finally {
      setBusy(false);
    }
  };

  const submitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editCourse || !editForm) return;
    setBusy(true);
    setError('');
    try {
      await api.adminUpdateCourse(editCourse.course_code, {
        name: editForm.name,
        category: editForm.category,
        workload: Number(editForm.workload),
        credits: Number(editForm.credits),
        prerequisites: editForm.prerequisites,
        skills: editForm.skills,
      });
      await loadCourses();
      closeEdit();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'העדכון נכשל');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (code: number) => {
    if (!window.confirm(`למחוק את הקורס ${code}? פעולה זו בלתי הפיכה.`)) return;
    setBusy(true);
    try {
      await api.adminDeleteCourse(code);
      await loadCourses();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'המחיקה נכשלה');
    } finally {
      setBusy(false);
    }
  };

  const changeRole = async (userId: number, role: string) => {
    try {
      await api.adminSetUserRole(userId, role);
      await loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'שינוי התפקיד נכשל');
    }
  };

  const shown = courses.filter(
    (c) => c.name?.includes(filter) || String(c.course_code).includes(filter),
  );

  return (
    <div className="flex flex-col gap-6" dir="rtl">
      <h1 className="text-2xl font-bold text-gray-800">ניהול מערכת</h1>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-600 rounded-lg px-4 py-2 text-sm">
          {error}
        </div>
      )}

      {/* Add course form */}
      <section className="glass-panel p-4 sm:p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">הוספת קורס</h2>
        <form onSubmit={submitCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>קוד קורס (7 ספרות)</label>
            <input
              className={inputClass}
              placeholder="לדוגמה: 1234567"
              value={createForm.course_code}
              required
              type="number"
              onChange={(e) => setCreateForm({ ...createForm, course_code: e.target.value })}
            />
          </div>
          <div>
            <label className={labelClass}>שם הקורס</label>
            <input
              className={inputClass}
              placeholder="שם הקורס"
              value={createForm.name}
              required
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </div>
          <div>
            <label className={labelClass}>קטגוריה</label>
            <select
              className={inputClass}
              value={createForm.category}
              onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
            >
              <option value="elective">בחירה</option>
              <option value="mandatory">חובה</option>
              <option value="seminar">סמינר</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>עומס שבועי (שעות)</label>
            <input
              className={inputClass}
              type="number"
              min={0}
              value={createForm.workload}
              onChange={(e) => setCreateForm({ ...createForm, workload: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className={labelClass}>נקודות זכות (נ"ז)</label>
            <input
              className={inputClass}
              type="number"
              step="0.5"
              min={0}
              value={createForm.credits}
              onChange={(e) => setCreateForm({ ...createForm, credits: Number(e.target.value) })}
            />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass}>כישורים (מופרדים בפסיק)</label>
            <input
              className={inputClass}
              placeholder="לדוגמה: Python, SQL, אלגוריתמים"
              value={createForm.skills}
              onChange={(e) => setCreateForm({ ...createForm, skills: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass}>דרישות קדם (טקסט חופשי)</label>
            <input
              className={inputClass}
              placeholder="לדוגמה: מבוא למדעי המחשב, מבני נתונים"
              value={createForm.prerequisites}
              onChange={(e) => setCreateForm({ ...createForm, prerequisites: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={busy}
              className="bg-emerald-600 hover:bg-emerald-500 text-white py-2 px-5 rounded-lg font-medium disabled:opacity-50 transition-colors"
            >
              צור קורס
            </button>
          </div>
        </form>
      </section>

      {/* Courses — card grid (same design as the explorer page) */}
      <section className="glass-panel p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between mb-4 gap-3">
          <h2 className="text-lg font-bold text-gray-800">קורסים ({courses.length})</h2>
          <input
            className={`${inputClass} max-w-xs`}
            placeholder="חיפוש לפי שם/קוד"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-6 items-stretch">
          {shown.map((course) => (
            <div
              key={course.course_code}
              className="glass-panel !p-4 flex flex-col items-center text-center h-full min-h-0"
            >
              <span className="inline-block text-[11px] font-mono bg-gray-100 px-2 py-0.5 rounded text-emerald-700 mb-2 shrink-0">
                {course.course_code}
              </span>
              <div className="mb-2 flex min-h-[3.25rem] w-full items-center justify-center shrink-0">
                <h3 className="text-base font-semibold leading-snug line-clamp-3 overflow-hidden w-full">
                  {course.name}
                </h3>
              </div>

              <div className="grid grid-cols-3 gap-1.5 mb-3 w-full shrink-0">
                <CourseStatBox label='נ"ז' value={course.credits} tone="emerald" />
                <CourseStatBox label="שעות" value={course.workload} sub="בשבוע" tone="blue" />
                <CourseStatBox
                  label="נוכחות"
                  value={course.mandatory_attendance ? 'חובה' : 'גמישה'}
                  tone={course.mandatory_attendance ? 'rose' : 'slate'}
                />
              </div>

              <div className="mt-auto flex w-full gap-2">
                <button
                  onClick={() => openEdit(course)}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-1.5 rounded-lg text-sm font-medium transition-colors"
                >
                  עריכה
                </button>
                <button
                  onClick={() => remove(course.course_code)}
                  className="flex-1 border border-red-200 bg-red-50 hover:bg-red-100 text-red-600 py-1.5 rounded-lg text-sm font-medium transition-colors"
                >
                  מחיקה
                </button>
              </div>
            </div>
          ))}
          {shown.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-400">
              לא נמצאו קורסים.
            </div>
          )}
        </div>
      </section>

      {/* User / role management */}
      <section className="glass-panel p-4 sm:p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">ניהול הרשאות משתמשים ({users.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-right">
            <thead className="text-gray-500 border-b border-gray-200">
              <tr>
                <th className="py-2 px-2">#</th>
                <th className="py-2 px-2">שם</th>
                <th className="py-2 px-2">אימייל</th>
                <th className="py-2 px-2">תפקיד</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 text-gray-500">{u.id}</td>
                  <td className="py-2 px-2 font-medium text-gray-800">{u.name}</td>
                  <td className="py-2 px-2 text-gray-500">{u.email}</td>
                  <td className="py-2 px-2">
                    <select
                      value={u.role}
                      onChange={(e) => changeRole(u.id, e.target.value)}
                      className="bg-gray-100 border border-gray-200 rounded-lg p-1 text-gray-800 focus:outline-none focus:border-emerald-400"
                    >
                      <option value="student">סטודנט</option>
                      <option value="admin">מנהל</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Edit course modal */}
      {editCourse && editForm && (
        <div className={courseModalOverlayClass} onClick={closeEdit}>
          <div
            className={courseModalShellClass}
            dir="rtl"
            onClick={(e) => e.stopPropagation()}
          >
            <CourseModalCloseButton onClose={closeEdit} />
            <div className="mb-6 text-center">
              <span className="inline-block bg-blue-500/20 px-3 py-1 rounded text-sm text-emerald-700 font-mono border border-blue-500/30 mb-2">
                {editCourse.course_code}
              </span>
              <h2 className="text-xl sm:text-2xl font-bold">עריכת קורס</h2>
            </div>
            <form onSubmit={submitEdit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className={labelClass}>שם הקורס</label>
                <input
                  className={inputClass}
                  value={editForm.name}
                  required
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>
              <div>
                <label className={labelClass}>קטגוריה</label>
                <select
                  className={inputClass}
                  value={editForm.category}
                  onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                >
                  <option value="elective">בחירה</option>
                  <option value="mandatory">חובה</option>
                  <option value="seminar">סמינר</option>
                </select>
              </div>
              <div>
                <label className={labelClass}>עומס שבועי (שעות)</label>
                <input
                  className={inputClass}
                  type="number"
                  min={0}
                  value={editForm.workload}
                  onChange={(e) => setEditForm({ ...editForm, workload: Number(e.target.value) })}
                />
              </div>
              <div>
                <label className={labelClass}>נקודות זכות (נ"ז)</label>
                <input
                  className={inputClass}
                  type="number"
                  step="0.5"
                  min={0}
                  value={editForm.credits}
                  onChange={(e) => setEditForm({ ...editForm, credits: Number(e.target.value) })}
                />
              </div>
              <div>
                <label className={labelClass}>כישורים (מופרדים בפסיק)</label>
                <input
                  className={inputClass}
                  value={editForm.skills}
                  onChange={(e) => setEditForm({ ...editForm, skills: e.target.value })}
                />
              </div>
              <div className="sm:col-span-2">
                <label className={labelClass}>דרישות קדם (טקסט חופשי)</label>
                <input
                  className={inputClass}
                  value={editForm.prerequisites}
                  onChange={(e) => setEditForm({ ...editForm, prerequisites: e.target.value })}
                />
              </div>
              <div className="sm:col-span-2 flex gap-2">
                <button
                  type="submit"
                  disabled={busy}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white py-2 px-5 rounded-lg font-medium disabled:opacity-50 transition-colors"
                >
                  שמור שינויים
                </button>
                <button
                  type="button"
                  onClick={closeEdit}
                  className="border border-gray-200 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-5 rounded-lg font-medium transition-colors"
                >
                  ביטול
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
