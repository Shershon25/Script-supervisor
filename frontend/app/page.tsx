'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Project, Scene, StoryStateResponse, IssueResponse,
  listProjects, createProject, deleteProject, listScenes, getStoryState, listIssues, seedDemoProject,
  analyzeScene, analyzeUnifiedScene, reviewIssue, updateSceneText
} from '@/lib/api';
import HeaderNav from '@/components/Layout/HeaderNav';
import SceneSidebar from '@/components/Scenes/SceneSidebar';
import ScreenplayPage from '@/components/Editor/ScreenplayPage';
import SupervisorPanel from '@/components/Supervisor/SupervisorPanel';
import ReasoningView from '@/components/Reasoning/ReasoningView';
import OutlineView from '@/components/Outline/OutlineView';
import CharactersView from '@/components/Characters/CharactersView';
import { TimelineView } from '@/components/Timeline/TimelineView';
import { SettingsView } from '@/components/Settings/SettingsView';
import { ToastProvider, useToast } from '@/components/UI/Toast';
import { Film, FolderPlus } from 'lucide-react';

function HomeContent() {
  const toast = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [activeSceneNumber, setActiveSceneNumber] = useState<number>(1);
  
  const [activeTab, setActiveTab] = useState<'editor' | 'outline' | 'characters' | 'reasoning' | 'timeline' | 'settings'>('editor');

  const [storyState, setStoryState] = useState<StoryStateResponse | null>(null);
  const [issues, setIssues] = useState<IssueResponse[]>([]);
  const [analyzedTextMap, setAnalyzedTextMap] = useState<Record<string, string>>({});
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');
  
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingDraftsRef = useRef<Record<string, string>>({});
  
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [supervisorCollapsed, setSupervisorCollapsed] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number; currentHeading?: string } | null>(null);
  const cancelBatchRef = useRef<boolean>(false);
  const [loadingData, setLoadingData] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('light');

  const [newTitle, setNewTitle] = useState('');
  const [creatingProject, setCreatingProject] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      const themeClass = theme === 'light' ? 'theme-light' : 'theme-dark';
      document.documentElement.className = theme === 'light' ? 'light theme-light' : 'dark theme-dark';
      document.body.className = `${themeClass} bg-app text-txtPrimary min-h-screen font-sans antialiased selection:bg-accent selection:text-white`;
    }
  }, [theme]);

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, []);

  const currentScene = scenes.find((s) => s.scene_number === activeSceneNumber) || scenes[0];
  const isStale = Boolean(currentScene && analyzedTextMap[currentScene.id] && analyzedTextMap[currentScene.id] !== currentScene.raw_text);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isCtrlOrCmd = e.ctrlKey || e.metaKey;
      
      // Ctrl/Cmd + S: Manual Force Save
      if (isCtrlOrCmd && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (currentScene?.id && activeProject && pendingDraftsRef.current[currentScene.id]) {
          flushPendingSave(activeProject.id, currentScene.id, currentScene.raw_text);
          toast.success('Scene Saved', `Scene #${activeSceneNumber} draft text saved to database.`);
        } else {
          toast.info('Up to Date', 'Current scene draft is already saved.');
        }
      }

      // Ctrl/Cmd + Shift + A: Trigger Active Scene AI Analysis
      if (isCtrlOrCmd && e.shiftKey && e.key.toLowerCase() === 'a') {
        e.preventDefault();
        handleAnalyzeActiveScene();
      }

      // Alt + 1..5: Instant Tab Navigation
      if (e.altKey) {
        if (e.key === '1') { e.preventDefault(); setActiveTab('editor'); }
        if (e.key === '2') { e.preventDefault(); setActiveTab('outline'); }
        if (e.key === '3') { e.preventDefault(); setActiveTab('characters'); }
        if (e.key === '4') { e.preventDefault(); setActiveTab('reasoning'); }
        if (e.key === '5') { e.preventDefault(); setActiveTab('timeline'); }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeProject, currentScene, activeSceneNumber]);

  async function fetchProjects() {
    try {
      const list = await listProjects();
      setProjects(list);
      if (list.length > 0 && !activeProject) {
        selectProject(list[0]);
      }
    } catch (e) {
      console.error("Error fetching projects", e);
    }
  }

  async function selectProject(proj: Project) {
    if (activeProject && currentScene?.id && pendingDraftsRef.current[currentScene.id]) {
      await flushPendingSave(activeProject.id, currentScene.id, currentScene.raw_text);
    }
    setActiveProject(proj);
    loadProjectData(proj.id);
  }

  async function loadProjectData(projectId: string) {
    setLoadingData(true);
    try {
      const [scenesList, currentStoryState, projectIssues] = await Promise.all([
        listScenes(projectId),
        getStoryState(projectId),
        listIssues(projectId)
      ]);

      // Check localStorage for un-flushed drafts
      const scenesWithDrafts = scenesList.map((sc) => {
        try {
          const cached = localStorage.getItem(`script_draft_${projectId}_${sc.id}`);
          if (cached) {
            return { ...sc, raw_text: cached };
          }
        } catch (e) {}
        return sc;
      });

      setScenes(scenesWithDrafts);
      setStoryState(currentStoryState);
      setIssues(projectIssues);
      
      // Initialize analyzedTextMap ONLY for scenes that have completed analysis
      setAnalyzedTextMap((prev) => {
        const updated = { ...prev };
        scenesList.forEach((s) => {
          if (s.is_analyzed && !updated[s.id]) {
            updated[s.id] = s.raw_text;
          }
        });
        return updated;
      });

      if (scenesList.length > 0 && !activeSceneNumber) {
        setActiveSceneNumber(scenesList[0].scene_number);
      }
    } catch (e) {
      console.error("Error loading project data", e);
    } finally {
      setLoadingData(false);
    }
  }

  async function flushPendingSave(projectId: string, sceneId: string, textToSave: string) {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }

    setSaveStatus('saving');
    try {
      await updateSceneText(projectId, sceneId, textToSave);
      delete pendingDraftsRef.current[sceneId];
      try {
        localStorage.removeItem(`script_draft_${projectId}_${sceneId}`);
      } catch (e) {}
      setSaveStatus('saved');
    } catch (err) {
      console.error('Failed to flush scene text to DB:', err);
      setSaveStatus('unsaved');
    }
  }

  function handleSceneTextChange(newText: string) {
    if (!currentScene?.id || !activeProject) return;

    // 1. Instant local state update for 0 typing latency
    setScenes(prev => prev.map(s => s.id === currentScene.id ? { ...s, raw_text: newText } : s));

    // 2. Instant Local Storage backup (0 network requests, crash-proof)
    const draftKey = `script_draft_${activeProject.id}_${currentScene.id}`;
    try {
      localStorage.setItem(draftKey, newText);
    } catch (e) {}

    pendingDraftsRef.current[currentScene.id] = newText;
    setSaveStatus('unsaved');

    // 3. Debounced DB save (3000ms delay - 3 seconds of typing inactivity)
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);

    saveTimerRef.current = setTimeout(() => {
      flushPendingSave(activeProject.id, currentScene.id, newText);
    }, 3000);
  }

  function handleBlurSave() {
    if (currentScene?.id && activeProject && pendingDraftsRef.current[currentScene.id]) {
      flushPendingSave(activeProject.id, currentScene.id, currentScene.raw_text);
    }
  }

  async function handleSelectSceneNumber(scNum: number) {
    if (scNum === activeSceneNumber) return;
    // Flush pending draft for active scene before switching scenes
    if (currentScene?.id && activeProject && pendingDraftsRef.current[currentScene.id]) {
      await flushPendingSave(activeProject.id, currentScene.id, currentScene.raw_text);
    }
    setActiveSceneNumber(scNum);
  }

  async function handleAnalyzeActiveScene() {
    if (!activeProject || !currentScene?.id) return;
    if (pendingDraftsRef.current[currentScene.id]) {
      await flushPendingSave(activeProject.id, currentScene.id, currentScene.raw_text);
    }
    setAnalyzing(true);
    try {
      // 1. Save scene text changes first
      await analyzeScene(activeProject.id, currentScene.scene_number, currentScene.raw_text);
      // 2. Trigger Unified Analysis Pipeline
      await analyzeUnifiedScene(activeProject.id, currentScene.id);
      // 3. Update analyzed text tracking hash
      setAnalyzedTextMap(prev => ({ ...prev, [currentScene.id]: currentScene.raw_text }));
      // 4. Refetch fresh issues & story state
      await loadProjectData(activeProject.id);
    } catch (err: any) {
      alert(err.message || 'Scene analysis failed');
    } finally {
      setAnalyzing(false);
    }
  }

  const handleStopAnalysis = () => {
    cancelBatchRef.current = true;
    toast.info('Stopping Analysis', 'Batch analysis will stop after the current scene finishes.');
  };

  async function handleAnalyzeAllScenes() {
    if (!activeProject || scenes.length === 0) return;
    setAnalyzing(true);
    cancelBatchRef.current = false;
    const sortedScenes = [...scenes].sort((a, b) => a.scene_number - b.scene_number);
    let completedCount = 0;

    try {
      for (let i = 0; i < sortedScenes.length; i++) {
        if (cancelBatchRef.current) {
          toast.warning('Analysis Stopped', `Batch analysis stopped after scene ${completedCount} of ${sortedScenes.length}. Progress preserved.`);
          break;
        }

        const sc = sortedScenes[i];
        setBatchProgress({
          current: i + 1,
          total: sortedScenes.length,
          currentHeading: sc.raw_text.split('\n')[0] || `Scene ${sc.scene_number}`
        });

        await analyzeScene(activeProject.id, sc.scene_number, sc.raw_text);
        await analyzeUnifiedScene(activeProject.id, sc.id);
        setAnalyzedTextMap(prev => ({ ...prev, [sc.id]: sc.raw_text }));
        completedCount++;

        // Refresh issues and story state after each scene completion
        await loadProjectData(activeProject.id);
      }

      if (!cancelBatchRef.current) {
        toast.success('Batch Analysis Complete', `Successfully analyzed all ${sortedScenes.length} scenes.`);
      }
    } catch (err: any) {
      toast.error('Batch Analysis Failed', err.message || 'Batch scene analysis failed');
    } finally {
      setAnalyzing(false);
      setBatchProgress(null);
      cancelBatchRef.current = false;
    }
  }

  const handleAddScene = async () => {
    if (!activeProject) return;
    const nextNum = scenes.length + 1;
    const defaultText = `INT. SCENE ${nextNum} - DAY\n\nJOHN enters the room.`;
    setAnalyzing(true);
    try {
      const res = await analyzeScene(activeProject.id, nextNum, defaultText);
      await analyzeUnifiedScene(activeProject.id, res.scene.id);
      await loadProjectData(activeProject.id);
      setActiveSceneNumber(nextNum);
    } catch (err: any) {
      alert(err.message || 'Failed to add scene');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReviewIssue = async (
    issueId: string,
    action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN',
    resolutionType?: string,
    note?: string
  ) => {
    if (!activeProject) return;
    try {
      const res = await reviewIssue(activeProject.id, issueId, action, resolutionType, note);
      setIssues((prev) => prev.map((i) => (i.id === issueId ? res.issue : i)));
      await loadProjectData(activeProject.id);
    } catch (err: any) {
      alert(err.message || 'Review action failed');
    }
  };

  const handleCreateInitialProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setCreatingProject(true);
    try {
      const proj = await createProject(newTitle.trim());
      setProjects([proj, ...projects]);
      setActiveProject(proj);
      setNewTitle('');
      loadProjectData(proj.id);
    } catch (err: any) {
      alert(err.message || 'Failed to create project');
    } finally {
      setCreatingProject(false);
    }
  };

  const handleLoadSampleProject = async () => {
    setCreatingProject(true);
    try {
      const sampleProj = await seedDemoProject();
      const list = await listProjects();
      setProjects(list);
      selectProject(sampleProj);
    } catch (err: any) {
      alert(err.message || 'Failed to load sample project');
    } finally {
      setCreatingProject(false);
    }
  };

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Pass all scene issues for the active scene so Supervisor Panel can toggle Audit History
  const activeSceneIssues = issues.filter(
    (i) => i.scene_number === activeSceneNumber
  );

  async function handleCreateProjectFromTitle(title: string) {
    const proj = await createProject(title);
    setProjects([proj, ...projects]);
    selectProject(proj);
  }

  async function handleDeleteProject(projectId: string) {
    try {
      await deleteProject(projectId);
      toast.success('Project Deleted', 'Project and all associated screenplay content deleted.');
      const updatedList = projects.filter((p) => p.id !== projectId);
      setProjects(updatedList);
      if (activeProject?.id === projectId) {
        if (updatedList.length > 0) {
          selectProject(updatedList[0]);
        } else {
          setActiveProject(null);
          setScenes([]);
          setStoryState(null);
          setIssues([]);
        }
      }
    } catch (err: any) {
      toast.error('Delete Failed', err.message || 'Failed to delete project');
    }
  }

  const activeSceneWords = currentScene?.raw_text ? currentScene.raw_text.trim().split(/\s+/).filter(Boolean).length : 0;
  const activeSceneLines = currentScene?.raw_text ? currentScene.raw_text.split('\n').length : 0;
  const totalProjectWords = scenes.reduce((acc, sc) => acc + (sc.raw_text ? sc.raw_text.trim().split(/\s+/).filter(Boolean).length : 0), 0);

  return (
    <div className={`h-screen max-h-screen overflow-hidden flex flex-col theme-${theme} bg-app text-txtPrimary transition-colors`}>
      {/* Top Header Navigation */}
      <HeaderNav
        projects={projects}
        activeProject={activeProject}
        onSelectProject={selectProject}
        onCreateProject={handleCreateProjectFromTitle}
        onDeleteProject={handleDeleteProject}
        onLoadDemoProject={handleLoadSampleProject}
        onImportSuccess={() => activeProject && loadProjectData(activeProject.id)}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        activeSceneNumber={activeSceneNumber}
        activeSceneHeading={currentScene?.raw_text.split('\n')[0] || ''}
        totalScenesCount={scenes.length}
        analyzing={analyzing}
        batchProgress={batchProgress}
        onStopAnalysis={handleStopAnalysis}
        isStale={isStale}
        saveStatus={saveStatus}
        onAnalyzeScene={handleAnalyzeActiveScene}
        onAnalyzeAllScenes={handleAnalyzeAllScenes}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main Content Workspace */}
      {!activeProject ? (
        <div className="flex-1 flex items-center justify-center p-6 min-h-0">
          <div className="p-8 rounded-3xl bg-card border border-border max-w-md w-full text-center space-y-6 shadow-2xl">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Film className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-txtPrimary">Script Supervisor Suite</h2>
              <p className="text-xs text-txtSecondary mt-1">
                Open an existing screenplay project or load the official demo project ("The Last Signal").
              </p>
            </div>

            <button
              onClick={handleLoadSampleProject}
              disabled={creatingProject}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50 text-xs"
            >
              <FolderPlus className="w-4 h-4" />
              <span>Load Demo Project ("The Last Signal")</span>
            </button>

            <form onSubmit={handleCreateInitialProject} className="space-y-3 text-left pt-2 border-t border-border">
              <input
                type="text"
                placeholder="New Project Title..."
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="w-full px-3.5 py-2 bg-panel border border-border rounded-xl text-xs text-txtPrimary placeholder-txtMuted focus:outline-none focus:border-secondary"
                required
              />
              <button
                type="submit"
                disabled={creatingProject || !newTitle.trim()}
                className="w-full py-2.5 bg-panel border border-border text-txtPrimary font-semibold rounded-xl text-xs hover:bg-cardHover transition-colors disabled:opacity-50"
              >
                Create Blank Project
              </button>
            </form>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden min-h-0 min-w-0">
          {/* Left Column: Scene Navigator */}
          <SceneSidebar
            scenes={scenes}
            activeSceneNumber={activeSceneNumber}
            issues={issues}
            onSelectScene={(s) => handleSelectSceneNumber(s.scene_number)}
            onAddScene={handleAddScene}
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          {/* Center Column: Screenplay Reader / Outline / Characters / Timeline */}
          {activeTab === 'editor' && currentScene ? (
            <ScreenplayPage
              sceneNumber={currentScene.scene_number}
              totalScenesCount={scenes.length}
              rawText={currentScene.raw_text}
              onChangeText={handleSceneTextChange}
              onBlurSave={handleBlurSave}
            />
          ) : activeTab === 'outline' ? (
            <OutlineView
              scenes={scenes}
              issues={issues}
              activeSceneNumber={activeSceneNumber}
              onSelectScene={(scNum) => {
                handleSelectSceneNumber(scNum);
                setActiveTab('editor');
              }}
            />
          ) : activeTab === 'characters' ? (
            <CharactersView
              storyState={storyState}
              onSelectSceneNumber={(scNum) => {
                handleSelectSceneNumber(scNum);
                setActiveTab('editor');
              }}
            />
          ) : activeTab === 'timeline' ? (
            <div className="flex-1 overflow-hidden flex flex-col min-h-0 min-w-0">
              <TimelineView
                projectId={activeProject.id}
                onNavigateToScene={(scNum) => {
                  handleSelectSceneNumber(scNum);
                  setActiveTab('editor');
                }}
              />
            </div>
          ) : activeTab === 'settings' ? (
            <div className="flex-1 overflow-y-auto">
              <SettingsView projectId={activeProject.id} />
            </div>
          ) : (
            <div className="flex-1 p-6 overflow-y-auto">
              <ReasoningView projectId={activeProject.id} scenes={scenes} />
            </div>
          )}


          {/* Right Column: SUPERVISOR Panel */}
          <SupervisorPanel
            projectId={activeProject.id}
            issues={issues}
            activeSceneNumber={activeSceneNumber}
            storyState={storyState}
            loading={loadingData}
            onSelectSceneNumber={(scNum) => handleSelectSceneNumber(scNum)}
            onReviewIssue={handleReviewIssue}
            collapsed={supervisorCollapsed}
            onToggleCollapse={() => setSupervisorCollapsed(!supervisorCollapsed)}
          />
        </div>
      )}

      {/* Bottom Status Bar with Dynamic Word and Line Metrics */}
      <footer className="h-7 border-t border bg-panel px-4 flex items-center justify-between text-[10px] font-mono text-txtSecondary select-none transition-colors">
        <div className="flex items-center space-x-3">
          <span>Scene {activeSceneNumber} of {scenes.length || 1}</span>
          <span>•</span>
          <span>Page {activeSceneNumber}</span>
          <span>•</span>
          <span>{activeSceneWords.toLocaleString()} words ({totalProjectWords.toLocaleString()} total)</span>
          <span>•</span>
          <span>{activeSceneLines} lines</span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            <span className={`w-1.5 h-1.5 rounded-full ${analyzing ? 'bg-tertiary animate-spin' : 'bg-secondary'}`} />
            <span>{analyzing ? 'Analyzing scene...' : 'Analysis synced'}</span>
          </div>
          <span>•</span>
          <span>Screenplay Format US Letter</span>
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <ToastProvider>
      <HomeContent />
    </ToastProvider>
  );
}
