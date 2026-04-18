import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Questionnaire() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [metadata, setMetadata] = useState({ tracks: [], job_roles: [] });
  const [profile, setProfile] = useState({
    target_workload: 3,
    needs_flexible_attendance: false,
    interested_track_ids: [] as int[],
    interested_job_role_ids: [] as int[]
  });

  useEffect(() => {
    if (user) {
      Promise.all([
        api.getMetadata(),
        api.getProfile(user.user_id)
      ]).then(([metaRes, profRes]) => {
        setMetadata(metaRes.data);
        const p = profRes.data;
        setProfile({
          target_workload: p.target_workload,
          needs_flexible_attendance: p.needs_flexible_attendance,
          interested_track_ids: p.interested_tracks.map((t: any) => t.id),
          interested_job_role_ids: p.interested_job_roles.map((r: any) => r.id)
        });
      }).catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await api.updateProfile(user.user_id, profile);
      navigate('/');
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const toggleSelection = (field: 'interested_track_ids' | 'interested_job_role_ids', id: number) => {
    setProfile(prev => {
      const current = prev[field];
      return {
        ...prev,
        [field]: current.includes(id) ? current.filter(x => x !== id) : [...current, id]
      };
    });
  };

  if (loading) return <div className="text-center mt-20">Loading your profile...</div>;

  return (
    <div className="max-w-2xl mx-auto glass-panel mt-10">
      <div className="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
        <h1 className="text-2xl font-bold">Your Preferences</h1>
        <div className="text-sm text-white/50">Step {step} of 3</div>
      </div>

      {step === 1 && (
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-xl font-semibold mb-4">What are your academic interests?</h2>
          <p className="text-white/60 text-sm mb-4">Select the tracks you find most interesting.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {metadata.tracks.map((track: any) => (
              <div 
                key={track.id}
                onClick={() => toggleSelection('interested_track_ids', track.id)}
                className={`p-4 rounded-xl cursor-pointer border transition-all ${
                  profile.interested_track_ids.includes(track.id) 
                  ? 'bg-blue-600/40 border-blue-400 shadow-lg shadow-blue-500/20' 
                  : 'bg-white/5 border-white/10 hover:bg-white/10'
                }`}
              >
                <div className="font-medium text-lg">{track.name}</div>
              </div>
            ))}
          </div>
          <div className="flex justify-end mt-8">
            <button onClick={() => setStep(2)} className="bg-white/10 hover:bg-white/20 px-6 py-2 rounded-lg">Next</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-xl font-semibold mb-4">Career Goals</h2>
          <p className="text-white/60 text-sm mb-4">What job roles are you aiming for?</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {metadata.job_roles.map((role: any) => (
              <div 
                key={role.id}
                onClick={() => toggleSelection('interested_job_role_ids', role.id)}
                className={`p-4 rounded-xl cursor-pointer border transition-all ${
                  profile.interested_job_role_ids.includes(role.id) 
                  ? 'bg-purple-600/40 border-purple-400 shadow-lg shadow-purple-500/20' 
                  : 'bg-white/5 border-white/10 hover:bg-white/10'
                }`}
              >
                <div className="font-medium text-lg">{role.title}</div>
                <div className="text-xs text-white/50 mt-1">Demand: {role.demand_level}</div>
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-8">
            <button onClick={() => setStep(1)} className="text-white/60 hover:text-white">Back</button>
            <button onClick={() => setStep(3)} className="bg-white/10 hover:bg-white/20 px-6 py-2 rounded-lg">Next</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-xl font-semibold mb-4">Logistics</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Target Workload (hours/week)</label>
              <input 
                type="number" 
                min="1" max="40"
                value={profile.target_workload}
                onChange={e => setProfile({...profile, target_workload: parseInt(e.target.value) || 0})}
                className="w-full bg-black/20 border border-white/10 rounded p-3 text-white focus:border-blue-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-3 pt-4">
              <input 
                type="checkbox" 
                id="flex"
                checked={profile.needs_flexible_attendance}
                onChange={e => setProfile({...profile, needs_flexible_attendance: e.target.checked})}
                className="w-5 h-5 accent-blue-500 cursor-pointer"
              />
              <label htmlFor="flex" className="cursor-pointer text-white/90">I need flexible attendance (prefer non-mandatory courses)</label>
            </div>
          </div>

          <div className="flex justify-between mt-8 pt-4 border-t border-white/10">
            <button onClick={() => setStep(2)} className="text-white/60 hover:text-white">Back</button>
            <button 
              onClick={handleSave} 
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-500 px-8 py-2 rounded-lg font-medium shadow-lg shadow-blue-500/30 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Finish & View Recommendations'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
