'use client';

import React, { useState, useEffect } from 'react';
import { 
  Sliders, Globe, ShieldAlert, Plus, Trash2, Edit2, Check, X, ToggleLeft, ToggleRight, 
  RefreshCw, Info, AlertTriangle, Save, RotateCcw
} from 'lucide-react';
import { 
  ProjectSettings, StoryWorldRule, getProjectSettings, updateProjectSettings, 
  createWorldRule, updateWorldRule, deleteWorldRule 
} from '@/lib/api';

interface SettingsViewProps {
  projectId: string;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ projectId }) => {
  const [settings, setSettings] = useState<ProjectSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Draft states for explicit batch save
  const [draftRealityLevel, setDraftRealityLevel] = useState<number>(5);
  const [draftContinuityStrictness, setDraftContinuityStrictness] = useState<number>(5);
  const [draftAutoBackgroundAnalysis, setDraftAutoBackgroundAnalysis] = useState<boolean>(true);
  const [draftWorldRules, setDraftWorldRules] = useState<StoryWorldRule[]>([]);

  // Confirmation Modal state
  const [confirmModalOpen, setConfirmModalOpen] = useState<boolean>(false);

  // New rule input state
  const [newRuleText, setNewRuleText] = useState<string>('');

  // Edit rule inline state
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [editRuleText, setEditRuleText] = useState<string>('');

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getProjectSettings(projectId);
      setSettings(res);
      setDraftRealityLevel(res.reality_level);
      setDraftContinuityStrictness(res.continuity_strictness);
      setDraftAutoBackgroundAnalysis(res.auto_background_analysis_enabled !== false);
      setDraftWorldRules(res.world_rules || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load project settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchSettings();
    }
  }, [projectId]);

  // Check if any sliders or rules have unsaved edits
  const isRulesDifferent = Boolean(
    settings && (
      draftWorldRules.length !== settings.world_rules.length ||
      JSON.stringify(draftWorldRules.map(r => ({ id: r.id, text: r.rule_text, active: r.active }))) !==
      JSON.stringify(settings.world_rules.map(r => ({ id: r.id, text: r.rule_text, active: r.active })))
    )
  );

  const hasUnsavedChanges = Boolean(
    settings && (
      draftRealityLevel !== settings.reality_level || 
      draftContinuityStrictness !== settings.continuity_strictness ||
      draftAutoBackgroundAnalysis !== (settings.auto_background_analysis_enabled !== false) ||
      isRulesDifferent
    )
  );

  const handleDiscardChanges = () => {
    if (!settings) return;
    setDraftRealityLevel(settings.reality_level);
    setDraftContinuityStrictness(settings.continuity_strictness);
    setDraftAutoBackgroundAnalysis(settings.auto_background_analysis_enabled !== false);
    setDraftWorldRules(settings.world_rules || []);
    setEditingRuleId(null);
    setEditRuleText('');
    setNewRuleText('');
  };

  // Local draft rule operations
  const handleAddWorldRuleDraft = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleText.trim()) return;

    const tempRule: StoryWorldRule = {
      id: `temp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      project_id: projectId,
      rule_text: newRuleText.trim(),
      active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    setDraftWorldRules(prev => [...prev, tempRule]);
    setNewRuleText('');
  };

  const handleToggleRuleDraft = (ruleId: string) => {
    setDraftWorldRules(prev => prev.map(r => r.id === ruleId ? { ...r, active: !r.active } : r));
  };

  const handleSaveEditRuleDraft = (ruleId: string) => {
    if (!editRuleText.trim()) return;
    setDraftWorldRules(prev => prev.map(r => r.id === ruleId ? { ...r, rule_text: editRuleText.trim() } : r));
    setEditingRuleId(null);
    setEditRuleText('');
  };

  const handleDeleteRuleDraft = (ruleId: string) => {
    setDraftWorldRules(prev => prev.filter(r => r.id !== ruleId));
  };

  const handleOpenConfirmModal = () => {
    if (!hasUnsavedChanges) return;
    setConfirmModalOpen(true);
  };

  const handleConfirmSave = async () => {
    if (!settings) return;
    try {
      setSaving(true);
      setError(null);

      // 1. Update sliders/settings if changed
      if (
        draftRealityLevel !== settings.reality_level ||
        draftContinuityStrictness !== settings.continuity_strictness ||
        draftAutoBackgroundAnalysis !== (settings.auto_background_analysis_enabled !== false)
      ) {
        await updateProjectSettings(projectId, draftRealityLevel, draftContinuityStrictness, draftAutoBackgroundAnalysis);
      }

      // 2. Reconcile World Rules
      const originalRulesMap = new Map(settings.world_rules.map(r => [r.id, r]));
      const draftRulesMap = new Map(draftWorldRules.map(r => [r.id, r]));

      // A. Delete removed rules
      for (const origRule of settings.world_rules) {
        if (!draftRulesMap.has(origRule.id)) {
          await deleteWorldRule(projectId, origRule.id);
        }
      }

      // B. Add new rules or update modified existing rules
      for (const draftRule of draftWorldRules) {
        if (draftRule.id.startsWith('temp_')) {
          // Newly added rule
          await createWorldRule(projectId, draftRule.rule_text, draftRule.active);
        } else {
          const orig = originalRulesMap.get(draftRule.id);
          if (orig && (orig.rule_text !== draftRule.rule_text || orig.active !== draftRule.active)) {
            // Updated rule
            await updateWorldRule(projectId, draftRule.id, draftRule.rule_text, draftRule.active);
          }
        }
      }

      // 3. Re-fetch clean updated settings
      const freshSettings = await getProjectSettings(projectId);
      setSettings(freshSettings);
      setDraftRealityLevel(freshSettings.reality_level);
      setDraftContinuityStrictness(freshSettings.continuity_strictness);
      setDraftWorldRules(freshSettings.world_rules || []);

      setConfirmModalOpen(false);
      setSuccessMessage('Project settings and Story World Rules saved successfully!');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings.');
    } finally {
      setSaving(false);
    }
  };

  const getRealityLabel = (level: number) => {
    if (level <= 2) return {
      title: 'Pure Sci-Fi / Fantasy',
      desc: 'Real-world physical laws, historical dates, and travel constraints do NOT apply. External research is disabled.',
      color: 'text-purple-700 dark:text-purple-300 bg-purple-500/10 border-purple-300 dark:border-purple-800/60'
    };
    if (level <= 5) return {
      title: 'Speculative / Soft Realism',
      desc: 'Fictional concepts and exaggerated timelines are allowed without flagging false reality errors.',
      color: 'text-blue-700 dark:text-blue-300 bg-blue-500/10 border-blue-300 dark:border-blue-800/60'
    };
    if (level <= 8) return {
      title: 'Grounded Realism',
      desc: 'Standard screenplay reality. Real-world geography, travel times, and historical facts are verified.',
      color: 'text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 border-emerald-300 dark:border-emerald-800/60'
    };
    return {
      title: 'Strict Documentary Realism',
      desc: 'Ultra-strict real-world fact enforcement. Every location, technology date, and law is rigorously researched.',
      color: 'text-amber-700 dark:text-amber-300 bg-amber-500/10 border-amber-300 dark:border-amber-800/60'
    };
  };

  const getStrictnessLabel = (level: number) => {
    if (level <= 2) return {
      title: 'Casual & Forgiving',
      desc: 'Flags only severe, indisputable contradictions (e.g. deceased character acting). Minor state shifts ignored.',
      color: 'text-purple-700 dark:text-purple-300 bg-purple-500/10 border-purple-300 dark:border-purple-800/60'
    };
    if (level <= 5) return {
      title: 'Standard Script Supervisor',
      desc: 'Balanced continuity tracking. Flags clear narrative conflicts and unexplained state jumps.',
      color: 'text-blue-700 dark:text-blue-300 bg-blue-500/10 border-blue-300 dark:border-blue-800/60'
    };
    if (level <= 8) return {
      title: 'Strict Narrative Logic',
      desc: 'High-precision continuity enforcement. Checks character knowledge acquisition, physical movements, and object ownership.',
      color: 'text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 border-emerald-300 dark:border-emerald-800/60'
    };
    return {
      title: 'Zero-Tolerance Script Supervisor',
      desc: 'Maximum sensitivity. Flags every potential inconsistency, timeline gap, or unmentioned physical transition.',
      color: 'text-rose-700 dark:text-rose-300 bg-rose-500/10 border-rose-300 dark:border-rose-800/60'
    };
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-txtMuted space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin text-secondary" />
        <p className="text-xs font-medium">Loading project settings & story world rules...</p>
      </div>
    );
  }

  if (error || !settings) {
    return (
      <div className="p-5 bg-red-500/10 border border-red-300 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 max-w-3xl mx-auto my-8">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
          <div>
            <h3 className="font-semibold text-sm">Error Loading Settings</h3>
            <p className="text-xs mt-0.5">{error || 'Project settings could not be retrieved.'}</p>
          </div>
        </div>
        <button
          onClick={fetchSettings}
          className="mt-3 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  const realityInfo = getRealityLabel(draftRealityLevel);
  const strictnessInfo = getStrictnessLabel(draftContinuityStrictness);

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-5 text-txtPrimary pb-16 relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-secondary" />
            <h1 className="text-xl font-bold tracking-tight text-txtPrimary">Project Settings</h1>
          </div>
          <p className="text-xs text-txtSecondary mt-0.5">
            Configure reality boundaries, continuity strictness, and universe rules for this screenplay project.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Discard changes button */}
          {hasUnsavedChanges && (
            <button
              onClick={handleDiscardChanges}
              className="px-3 py-1.5 bg-panel border border-border hover:bg-cardHover text-txtSecondary rounded-lg text-xs font-medium flex items-center gap-1 transition"
              title="Discard unsaved edits"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Discard
            </button>
          )}

          {/* Explicit Save Settings Button */}
          <button
            onClick={handleOpenConfirmModal}
            disabled={!hasUnsavedChanges || saving}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all ${
              hasUnsavedChanges
                ? 'bg-blue-600 hover:bg-blue-500 text-white ring-2 ring-blue-500/30'
                : 'bg-panel border border-border text-txtMuted cursor-not-allowed opacity-60'
            }`}
          >
            {saving ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            <span>{hasUnsavedChanges ? 'Save Settings' : 'Saved'}</span>
            {hasUnsavedChanges && <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse ml-0.5" />}
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-300 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-300 rounded-xl text-xs flex items-center justify-between transition animate-fade-in">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-500" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-txtMuted hover:text-txtPrimary">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* TOP ROW: Grid for Reality Level (Left) & Continuity Strictness (Right) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Reality Level */}
        <section className={`bg-card border rounded-xl p-4 space-y-3.5 shadow-sm transition-colors ${draftRealityLevel !== settings.reality_level ? 'border-blue-500/50' : 'border-border'}`}>
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-600 dark:text-blue-400">
                <Globe className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-txtPrimary">Reality Level</h2>
                <p className="text-[11px] text-txtSecondary">Fact verification & web research gating</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              {draftRealityLevel !== settings.reality_level && (
                <span className="text-[10px] text-tertiary font-semibold uppercase tracking-wider">Unsaved</span>
              )}
              <span className="text-sm font-bold text-blue-600 dark:text-blue-400 px-2.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                {draftRealityLevel} / 10
              </span>
            </div>
          </div>

          {/* Dynamic Badge */}
          <div className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${realityInfo.color}`}>
            <Info className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold">{realityInfo.title}</div>
              <div className="text-[11px] opacity-90 mt-0.5 leading-snug">{realityInfo.desc}</div>
            </div>
          </div>

          {/* Slider */}
          <div className="space-y-1 pt-1">
            <input
              type="range"
              min={0}
              max={10}
              step={1}
              value={draftRealityLevel}
              onChange={(e) => setDraftRealityLevel(parseInt(e.target.value))}
              className="w-full h-1.5 bg-panel rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-[10px] text-txtMuted font-mono">
              <span>0 (Fantasy)</span>
              <span>5 (Balanced)</span>
              <span>10 (Docu)</span>
            </div>
          </div>
        </section>

        {/* Continuity Strictness */}
        <section className={`bg-card border rounded-xl p-4 space-y-3.5 shadow-sm transition-colors ${draftContinuityStrictness !== settings.continuity_strictness ? 'border-amber-500/50' : 'border-border'}`}>
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-600 dark:text-amber-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-txtPrimary">Continuity Strictness</h2>
                <p className="text-[11px] text-txtSecondary">Conflict evaluation sensitivity</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              {draftContinuityStrictness !== settings.continuity_strictness && (
                <span className="text-[10px] text-tertiary font-semibold uppercase tracking-wider">Unsaved</span>
              )}
              <span className="text-sm font-bold text-amber-600 dark:text-amber-400 px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                {draftContinuityStrictness} / 10
              </span>
            </div>
          </div>

          {/* Dynamic Badge */}
          <div className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${strictnessInfo.color}`}>
            <Info className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold">{strictnessInfo.title}</div>
              <div className="text-[11px] opacity-90 mt-0.5 leading-snug">{strictnessInfo.desc}</div>
            </div>
          </div>

          {/* Slider */}
          <div className="space-y-1 pt-1">
            <input
              type="range"
              min={0}
              max={10}
              step={1}
              value={draftContinuityStrictness}
              onChange={(e) => setDraftContinuityStrictness(parseInt(e.target.value))}
              className="w-full h-1.5 bg-panel rounded-lg appearance-none cursor-pointer accent-amber-600"
            />
            <div className="flex justify-between text-[10px] text-txtMuted font-mono">
              <span>0 (Casual)</span>
              <span>5 (Standard)</span>
              <span>10 (Zero-Tol)</span>
            </div>
          </div>
        </section>
      </div>

      {/* MIDDLE ROW: Auto Background Analysis Setting */}
      <section className={`bg-card border rounded-xl p-4 shadow-sm transition-colors ${draftAutoBackgroundAnalysis !== (settings.auto_background_analysis_enabled !== false) ? 'border-emerald-500/50' : 'border-border'}`}>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-600 dark:text-emerald-400 shrink-0">
              <RefreshCw className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-txtPrimary">Automatic Background Scene Analysis</h2>
                {draftAutoBackgroundAnalysis !== (settings.auto_background_analysis_enabled !== false) && (
                  <span className="text-[10px] text-tertiary font-semibold uppercase tracking-wider">Unsaved</span>
                )}
              </div>
              <p className="text-xs text-txtSecondary mt-0.5">
                Automatically evaluate the previous scene in the background when a new scene is added.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDraftAutoBackgroundAnalysis(!draftAutoBackgroundAnalysis)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-panel hover:bg-cardHover text-xs font-semibold transition shrink-0"
          >
            {draftAutoBackgroundAnalysis ? (
              <>
                <ToggleRight className="w-5 h-5 text-emerald-500" />
                <span className="text-emerald-600 dark:text-emerald-400">Enabled</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-5 h-5 text-txtMuted" />
                <span className="text-txtMuted">Disabled</span>
              </>
            )}
          </button>
        </div>
      </section>

      {/* BOTTOM ROW: Story World Rules */}
      <section className={`bg-card border rounded-xl p-5 space-y-4 shadow-sm transition-colors ${isRulesDifferent ? 'border-indigo-500/50' : 'border-border'}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-600 dark:text-indigo-400">
              <Globe className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-txtPrimary">Story World Rules</h2>
                {isRulesDifferent && (
                  <span className="text-[10px] text-tertiary font-semibold uppercase tracking-wider">Unsaved Edits</span>
                )}
              </div>
              <p className="text-xs text-txtSecondary">
                Explicit universe rules defined by the writer (overrides real-world physics and standard reality checking).
              </p>
            </div>
          </div>
          <span className="px-2.5 py-0.5 bg-panel border border-border text-txtSecondary text-xs font-medium rounded-md shrink-0">
            {draftWorldRules.filter(r => r.active).length} Active Rule{draftWorldRules.filter(r => r.active).length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Add New Rule Form */}
        <form onSubmit={handleAddWorldRuleDraft} className="flex gap-2">
          <input
            type="text"
            value={newRuleText}
            onChange={(e) => setNewRuleText(e.target.value)}
            placeholder="e.g. 'Teleportation device exists in this world' or 'Magic spells require verbal incantation'"
            className="flex-1 px-3.5 py-2 bg-panel border border-border rounded-lg text-xs text-txtPrimary placeholder:text-txtMuted focus:outline-none focus:border-secondary transition"
          />
          <button
            type="submit"
            disabled={!newRuleText.trim()}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg flex items-center gap-1.5 transition shrink-0 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Rule
          </button>
        </form>

        {/* Rules List */}
        <div className="space-y-2">
          {draftWorldRules.length === 0 ? (
            <div className="p-4 bg-panel/50 border border-dashed border-border rounded-lg text-center text-txtMuted text-xs">
              No Story World Rules defined yet. Add explicit rules above for fictional tech, magic, or physical laws.
            </div>
          ) : (
            draftWorldRules.map((rule) => (
              <div
                key={rule.id}
                className={`flex items-center justify-between p-3 rounded-lg border transition ${
                  rule.active
                    ? 'bg-panel/80 border-border text-txtPrimary'
                    : 'bg-panel/30 border-border/50 text-txtMuted'
                }`}
              >
                <div className="flex items-center gap-2.5 flex-1 mr-3">
                  <button
                    onClick={() => handleToggleRuleDraft(rule.id)}
                    className="text-txtMuted hover:text-txtPrimary transition shrink-0"
                    title={rule.active ? 'Disable rule' : 'Enable rule'}
                  >
                    {rule.active ? (
                      <ToggleRight className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-txtMuted" />
                    )}
                  </button>

                  {editingRuleId === rule.id ? (
                    <div className="flex items-center gap-2 flex-1">
                      <input
                        type="text"
                        value={editRuleText}
                        onChange={(e) => setEditRuleText(e.target.value)}
                        className="flex-1 px-2.5 py-1 bg-card border border-secondary rounded-md text-xs text-txtPrimary focus:outline-none"
                      />
                      <button
                        onClick={() => handleSaveEditRuleDraft(rule.id)}
                        className="p-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md transition"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => { setEditingRuleId(null); setEditRuleText(''); }}
                        className="p-1 bg-panel border border-border text-txtSecondary hover:text-txtPrimary rounded-md transition"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className={`text-xs ${rule.active ? 'text-txtPrimary font-medium' : 'text-txtMuted line-through'}`}>
                        {rule.rule_text}
                      </span>
                      {rule.id.startsWith('temp_') && (
                        <span className="px-1.5 py-0.2 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[9px] font-semibold rounded">
                          New
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {editingRuleId !== rule.id && (
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => { setEditingRuleId(rule.id); setEditRuleText(rule.rule_text); }}
                      className="p-1 text-txtMuted hover:text-secondary rounded-md transition"
                      title="Edit Rule"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteRuleDraft(rule.id)}
                      className="p-1 text-txtMuted hover:text-red-500 rounded-md transition"
                      title="Delete Rule"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </section>

      {/* Confirmation Modal */}
      {confirmModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5 text-txtPrimary relative">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-600 dark:text-blue-400 shrink-0">
                <Save className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-txtPrimary">Confirm Settings Update</h3>
                <p className="text-xs text-txtSecondary">Confirm your project choices before saving.</p>
              </div>
            </div>

            <div className="space-y-3 bg-panel p-4 rounded-xl border border-border text-xs">
              {draftRealityLevel !== settings.reality_level && (
                <div className="flex justify-between items-center pb-2 border-b border-border">
                  <span className="text-txtSecondary font-medium">Reality Level:</span>
                  <div className="flex items-center gap-2 font-bold font-mono">
                    <span className="text-txtMuted line-through">{settings.reality_level}</span>
                    <span className="text-secondary">→</span>
                    <span className="text-blue-600 dark:text-blue-400">{draftRealityLevel} / 10</span>
                  </div>
                </div>
              )}

              {draftContinuityStrictness !== settings.continuity_strictness && (
                <div className="flex justify-between items-center pb-2 border-b border-border">
                  <span className="text-txtSecondary font-medium">Continuity Strictness:</span>
                  <div className="flex items-center gap-2 font-bold font-mono">
                    <span className="text-txtMuted line-through">{settings.continuity_strictness}</span>
                    <span className="text-secondary">→</span>
                    <span className="text-amber-600 dark:text-amber-400">{draftContinuityStrictness} / 10</span>
                  </div>
                </div>
              )}

              {isRulesDifferent && (
                <div className="pt-1">
                  <span className="text-txtSecondary font-medium block mb-1">Story World Rules:</span>
                  <p className="text-[11px] text-txtMuted font-mono">
                    {draftWorldRules.length} rules queued ({draftWorldRules.filter(r => r.active).length} active).
                  </p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                onClick={() => setConfirmModalOpen(false)}
                className="px-4 py-2 bg-panel border border-border text-txtSecondary hover:text-txtPrimary rounded-xl text-xs font-semibold transition"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                Confirm & Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
