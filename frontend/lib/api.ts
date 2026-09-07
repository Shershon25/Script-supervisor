const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Project {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Scene {
  id: string;
  project_id: string;
  scene_number: number;
  raw_text: string;
  is_analyzed?: boolean;
  created_at: string;
  updated_at: string;
}

export interface EntityExtraction {
  type: 'character' | 'location' | 'object' | 'organization' | string;
  name: string;
  attributes: Record<string, any> | any[];
}

export interface FactExtraction {
  subject: string;
  predicate: string;
  value: string;
  confidence: number;
}

export interface EventExtraction {
  event_type: string;
  actor?: string;
  target?: string;
  location?: string;
  description: string;
}

export interface RelationshipExtraction {
  source: string;
  relationship_type: string;
  target?: string;
  confidence: number;
}

export interface KnowledgeChangeExtraction {
  character: string;
  knowledge: string;
  knowledge_type: string;
  confidence: number;
}

export interface SceneAnalysis {
  scene_summary: string;
  entities: EntityExtraction[];
  facts: FactExtraction[];
  events: EventExtraction[];
  relationships: RelationshipExtraction[];
  knowledge_changes: KnowledgeChangeExtraction[];
  claims?: any[];
}

// --- Story State Domain Interfaces ---

export interface EntityReference {
  id: string;
  name: string;
}

export interface RelationshipState {
  id: string;
  source: EntityReference;
  relationship_type: string;
  target?: EntityReference;
  source_scene_id: string;
  source_scene_number?: number;
  confidence: number;
}

export interface KnowledgeStateItem {
  id: string;
  character: EntityReference;
  knowledge: string;
  source_scene_id: string;
  source_scene_number?: number;
  knowledge_type: string;
  confidence: number;
}

export interface CharacterState {
  id: string;
  name: string;
  attributes: Record<string, any>;
  residence?: string;
  current_location?: EntityReference;
  possessions: EntityReference[];
  relationships: RelationshipState[];
  knowledge: KnowledgeStateItem[];
}

export interface LocationState {
  id: string;
  name: string;
  type?: string;
  attributes: Record<string, any>;
}

export interface ObjectState {
  id: string;
  name: string;
  type?: string;
  attributes: Record<string, any>;
  current_owner?: EntityReference;
  current_location?: EntityReference;
}

export interface FactState {
  id: string;
  subject: EntityReference;
  predicate: string;
  value: any;
  source_scene_id: string;
  source_scene_number?: number;
  confidence: number;
}

export interface EventState {
  id: string;
  scene_id: string;
  scene_number?: number;
  event_type: string;
  actor?: EntityReference;
  target?: EntityReference;
  location?: EntityReference;
  description: string;
  attributes: Record<string, any>;
}

export interface StoryStateResponse {
  project_id: string;
  characters: CharacterState[];
  locations: LocationState[];
  objects: ObjectState[];
  facts: FactState[];
  events: EventState[];
  relationships: RelationshipState[];
  knowledge_states: KnowledgeStateItem[];
}

// --- Day 3 & Day 4 Continuity Issue Interfaces ---

export interface IssueEvidence {
  scene_id: string;
  scene_number?: number;
  type: string;
  text: string;
}

export interface IssueReviewResponse {
  id: string;
  issue_id: string;
  project_id: string;
  action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN' | string;
  note?: string;
  previous_status: string;
  new_status: string;
  created_at: string;
}

export interface IssueResponse {
  id: string;
  project_id: string;
  scene_id: string;
  scene_number?: number;
  issue_type: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | string;
  title: string;
  description: string;
  confidence: number;
  status: 'OPEN' | 'ACCEPTED' | 'IGNORED' | 'RESOLVED' | string;
  evidence: IssueEvidence[];
  reviewed_at?: string;
  reviewed_by?: string;
  resolution_type?: 'INTENTIONAL' | 'FIXED' | 'FALSE_POSITIVE' | 'ACCEPTED_AS_IS' | 'NEEDS_REVIEW' | string;
  resolution_note?: string;
  issue_fingerprint?: string;
  reviews?: IssueReviewResponse[];
  created_at: string;
}

export interface IssueSummaryResponse {
  total: number;
  open: number;
  accepted: number;
  resolved: number;
  ignored: number;
  errors: number;
  warnings: number;
  info: number;
}

// --- Day 5 External Claims & Research Interfaces ---

export interface ClaimResponse {
  id: string;
  project_id: string;
  scene_id: string;
  scene_number?: number;
  claim_text: string;
  claim_type: 'REAL_WORLD_CLAIM' | 'FICTIONAL_WORLD_RULE' | 'STORY_FACT' | 'UNVERIFIED_CLAIM' | string;
  subject?: string;
  predicate?: string;
  object?: string;
  temporal_context?: string;
  location_context?: string;
  requires_research: boolean;
  research_priority: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  status: 'UNVERIFIED' | 'RESEARCH_REQUESTED' | 'VERIFIED' | 'LIKELY_TRUE' | 'CONTRADICTED' | 'INCONCLUSIVE' | 'DISMISSED' | string;
  claim_fingerprint?: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchSourceResponse {
  id: string;
  research_task_id: string;
  title: string;
  url: string;
  domain: string;
  excerpt: string;
  relevance_score: number;
  retrieved_at: string;
}

export interface ResearchEvaluationResponse {
  id: string;
  research_task_id: string;
  claim_id: string;
  verdict: 'VERIFIED' | 'LIKELY_TRUE' | 'CONTRADICTED' | 'INCONCLUSIVE' | 'INSUFFICIENT_EVIDENCE' | string;
  confidence: number;
  summary: string;
  reasoning: string;
  supporting_source_ids: string[];
  contradicting_source_ids: string[];
  created_at: string;
}

export interface ResearchTaskResponse {
  id: string;
  project_id: string;
  scene_id: string;
  claim_id: string;
  objective: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | string;
  provider: string;
  requested_at?: string;
  completed_at?: string;
  error_message?: string;
  claim?: ClaimResponse;
  sources: ResearchSourceResponse[];
  evaluation?: ResearchEvaluationResponse;
  created_at: string;
  updated_at: string;
}

// --- Day 6 Hybrid Retrieval & Reasoning Interfaces ---

export interface RetrievedItem {
  item_type: 'FACT' | 'EVENT' | 'RELATIONSHIP' | 'KNOWLEDGE' | 'WRITER_DECISION' | 'RESEARCH' | 'SCENE' | string;
  source_id: string;
  scene_id?: string;
  scene_number?: number;
  title: string;
  content: string;
  provenance_tag: string;
  relevance_score: number;
  retrieval_reason: string;
}

export interface RetrievalResponse {
  project_id: string;
  scene_id: string;
  scene_number?: number;
  task_type: string;
  total_retrieved: number;
  items: RetrievedItem[];
}

export interface ReasoningResult {
  task_type: string;
  scene_id: string;
  conclusion: string;
  verdict: 'NO_CONFLICT' | 'CONFLICT' | 'AMBIGUOUS' | 'VERIFIED' | 'CONTRADICTED' | string;
  confidence: number;
  summary: string;
  reasoning_summary: string;
  evidence_items: RetrievedItem[];
  writer_decision_context?: string;
}

export interface AnalyzeResponse {
  scene: Scene;
  analysis: SceneAnalysis;
  story_state?: StoryStateResponse;
  issues?: IssueResponse[];
}

// --- Day 7 Unified Script Supervisor Interfaces ---

export interface UnifiedAnalysisRunSummary {
  entities_count: number;
  facts_count: number;
  events_count: number;
  issues_count: number;
  claims_count: number;
  research_reused_count: number;
}

export interface UnifiedAnalysisResponse {
  run_id: string;
  project_id: string;
  scene_id: string;
  scene_number: number;
  status: 'IDLE' | 'ANALYZING' | 'COMPLETED' | 'PARTIAL' | 'FAILED' | string;
  summary: UnifiedAnalysisRunSummary;
  entities_detected: string[];
  issues_created: number;
  research_tasks_created: number;
  error_message?: string;
  started_at: string;
  completed_at: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/health`);
  return handleResponse<{ status: string }>(res);
}

export async function resetDb(projectId?: string): Promise<{ status: string; message: string }> {
  const url = projectId 
    ? `${API_URL}/api/reset-db?project_id=${encodeURIComponent(projectId)}`
    : `${API_URL}/api/reset-db`;
  const res = await fetch(url, { method: 'DELETE' });
  return handleResponse<{ status: string; message: string }>(res);
}

export async function listProjects(): Promise<Project[]> {
  const res = await fetch(`${API_URL}/api/projects`);
  return handleResponse<Project[]>(res);
}

export async function createProject(title: string): Promise<Project> {
  const res = await fetch(`${API_URL}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return handleResponse<Project>(res);
}

export async function getProject(id: string): Promise<Project> {
  const res = await fetch(`${API_URL}/api/projects/${id}`);
  return handleResponse<Project>(res);
}

export async function deleteProject(id: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_URL}/api/projects/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ status: string; message: string }>(res);
}

export async function renameProject(id: string, title: string): Promise<Project> {
  const res = await fetch(`${API_URL}/api/projects/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return handleResponse<Project>(res);
}

export async function listScenes(projectId: string): Promise<Scene[]> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/scenes`);
  return handleResponse<Scene[]>(res);
}

export async function updateSceneText(
  projectId: string,
  sceneId: string,
  rawText: string
): Promise<Scene> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/scenes/${sceneId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: rawText }),
  });
  return handleResponse<Scene>(res);
}

export async function analyzeScene(
  projectId: string,
  sceneNumber: number,
  rawText: string
): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/scenes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scene_number: sceneNumber, raw_text: rawText }),
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function analyzeUnifiedScene(
  projectId: string,
  sceneId: string
): Promise<UnifiedAnalysisResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/scenes/${sceneId}/analyze`, {
    method: 'POST'
  });
  return handleResponse<UnifiedAnalysisResponse>(res);
}

export async function getStoryState(projectId: string): Promise<StoryStateResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/story-state`);
  return handleResponse<StoryStateResponse>(res);
}

export async function listIssues(
  projectId: string,
  statusFilter?: string,
  severityFilter?: string
): Promise<IssueResponse[]> {
  const params = new URLSearchParams();
  if (statusFilter) params.append('status', statusFilter);
  if (severityFilter) params.append('severity', severityFilter);

  const res = await fetch(`${API_URL}/api/projects/${projectId}/issues?${params.toString()}`);
  return handleResponse<IssueResponse[]>(res);
}

export async function getIssueSummary(projectId: string): Promise<IssueSummaryResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/issues/summary`);
  return handleResponse<IssueSummaryResponse>(res);
}

export async function getIssue(projectId: string, issueId: string): Promise<IssueResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/issues/${issueId}`);
  return handleResponse<IssueResponse>(res);
}

export async function reviewIssue(
  projectId: string,
  issueId: string,
  action: 'ACCEPT' | 'IGNORE' | 'RESOLVE' | 'REOPEN',
  resolutionType?: string,
  note?: string
): Promise<{ issue: IssueResponse; review: IssueReviewResponse }> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/issues/${issueId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action,
      resolution_type: resolutionType,
      note,
    }),
  });
  return handleResponse<{ issue: IssueResponse; review: IssueReviewResponse }>(res);
}

export async function getIssueHistory(projectId: string, issueId: string): Promise<IssueReviewResponse[]> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/issues/${issueId}/history`);
  return handleResponse<IssueReviewResponse[]>(res);
}

// --- Day 5 Claims & Research API ---

export async function listClaims(
  projectId: string,
  claimType?: string,
  statusFilter?: string,
  requiresResearch?: boolean
): Promise<ClaimResponse[]> {
  const params = new URLSearchParams();
  if (claimType) params.append('claim_type', claimType);
  if (statusFilter) params.append('status', statusFilter);
  if (requiresResearch !== undefined) params.append('requires_research', String(requiresResearch));

  const res = await fetch(`${API_URL}/api/projects/${projectId}/claims?${params.toString()}`);
  return handleResponse<ClaimResponse[]>(res);
}

export async function triggerResearch(
  projectId: string,
  claimId: string,
  forceRefresh: boolean = false
): Promise<{ status: string; task_id: string; verdict: string; confidence: number; summary: string }> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/claims/${claimId}/research?force_refresh=${forceRefresh}`, {
    method: 'POST'
  });
  return handleResponse<{ status: string; task_id: string; verdict: string; confidence: number; summary: string }>(res);
}

export async function getResearchTask(
  projectId: string,
  researchTaskId: string
): Promise<ResearchTaskResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/research/${researchTaskId}`);
  return handleResponse<ResearchTaskResponse>(res);
}

export async function listResearchTasks(
  projectId: string
): Promise<ResearchTaskResponse[]> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/research`);
  return handleResponse<ResearchTaskResponse[]>(res);
}

// --- Day 6 Context Retrieval & AI Reasoning API ---

export async function retrieveContext(
  projectId: string,
  sceneId: string,
  taskType: string = 'CONTINUITY',
  entityNames: string[] = []
): Promise<RetrievalResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/retrieve-context`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scene_id: sceneId, task_type: taskType, entity_names: entityNames })
  });
  return handleResponse<RetrievalResponse>(res);
}

export async function runReasoning(
  projectId: string,
  sceneId: string,
  taskType: string = 'CONTINUITY',
  targetEntityNames: string[] = [],
  question?: string
): Promise<ReasoningResult> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/reason`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scene_id: sceneId,
      task_type: taskType,
      target_entity_names: targetEntityNames,
      question
    })
  });
  return handleResponse<ReasoningResult>(res);
}

// --- Plot Structure Timeline Visualizer API ---

export interface PlotEventItem {
  event_id: string;
  scene_number: number;
  title: string;
  description: string;
  track_type: 'MAIN_PLOT' | 'SUBPLOT' | string;
  track_name: string;
  importance_score: 'CRITICAL' | 'HIGH' | 'MEDIUM' | string;
  excerpt: string;
  connected_to_event?: string | null;
  connection_type?: 'TRIGGERS' | 'CONVERGES_WITH' | 'REVEALS' | 'CONTRADICTS' | string | null;
}

export interface TimelineViewResponse {
  project_id: string;
  events: PlotEventItem[];
  tracks: string[];
}

export async function getTimeline(projectId: string): Promise<TimelineViewResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/timeline`);
  return handleResponse<TimelineViewResponse>(res);
}

export async function extractTimeline(projectId: string): Promise<TimelineViewResponse> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/timeline/extract`, {
    method: 'POST'
  });
  return handleResponse<TimelineViewResponse>(res);
}

// --- Project Settings & Story World Rules API ---

export interface StoryWorldRule {
  id: string;
  project_id: string;
  rule_text: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectSettings {
  id: string;
  project_id: string;
  reality_level: number;
  continuity_strictness: number;
  auto_background_analysis_enabled?: boolean;
  settings_version: number;
  world_rules: StoryWorldRule[];
  created_at: string;
  updated_at: string;
}

export async function getProjectSettings(projectId: string): Promise<ProjectSettings> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/settings`);
  return handleResponse<ProjectSettings>(res);
}

export async function updateProjectSettings(
  projectId: string,
  realityLevel?: number,
  continuityStrictness?: number,
  autoBackgroundAnalysisEnabled?: boolean
): Promise<ProjectSettings> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      reality_level: realityLevel,
      continuity_strictness: continuityStrictness,
      auto_background_analysis_enabled: autoBackgroundAnalysisEnabled
    })
  });
  return handleResponse<ProjectSettings>(res);
}

export async function createWorldRule(
  projectId: string,
  ruleText: string,
  active: boolean = true
): Promise<StoryWorldRule> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/settings/world-rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rule_text: ruleText, active })
  });
  return handleResponse<StoryWorldRule>(res);
}

export async function updateWorldRule(
  projectId: string,
  ruleId: string,
  ruleText?: string,
  active?: boolean
): Promise<StoryWorldRule> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/settings/world-rules/${ruleId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rule_text: ruleText, active })
  });
  return handleResponse<StoryWorldRule>(res);
}

export async function deleteWorldRule(
  projectId: string,
  ruleId: string
): Promise<void> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/settings/world-rules/${ruleId}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    throw new Error(`Failed to delete world rule '${ruleId}'`);
  }
}

// --- Document Import Domain Interfaces & API Client ---

export interface ParsedScene {
  temporary_id: string;
  scene_number: number;
  heading: string;
  raw_text: string;
  source_page_start?: number | null;
  source_page_end?: number | null;
  confidence: number;
}

export interface ImportPreview {
  document_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  page_count?: number | null;
  character_count: number;
  scene_count: number;
  scenes: ParsedScene[];
  warnings: string[];
  existing_scenes_count: number;
}

export interface ImportedDocument {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  parser_version: string;
  scene_detection_version: string;
  error_message?: string | null;
  page_count?: number | null;
  character_count?: number | null;
  scene_count?: number | null;
  created_at: string;
  updated_at: string;
}

export async function uploadDocumentForPreview(
  projectId: string,
  file: File
): Promise<ImportPreview> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/api/projects/${projectId}/documents/import`, {
    method: 'POST',
    body: formData
  });
  return handleResponse<ImportPreview>(res);
}

export async function confirmDocumentImport(
  projectId: string,
  documentId: string,
  mode: 'append' | 'replace' = 'append'
): Promise<{ message: string; document_id: string; scenes_imported: number }> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/documents/${documentId}/confirm-import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  });
  return handleResponse<{ message: string; document_id: string; scenes_imported: number }>(res);
}

export async function listImportedDocuments(
  projectId: string
): Promise<ImportedDocument[]> {
  const res = await fetch(`${API_URL}/api/projects/${projectId}/documents`);
  return handleResponse<ImportedDocument[]>(res);
}

export function getExportUrl(
  projectId: string,
  format: 'pdf' | 'docx' | 'fountain' = 'pdf',
  fontFamily: string = 'Courier',
  fontSize: number = 12
): string {
  const params = new URLSearchParams({
    format,
    font_family: fontFamily,
    font_size: fontSize.toString()
  });
  return `${API_URL}/api/projects/${projectId}/export?${params.toString()}`;
}

export function downloadProjectScript(
  projectId: string,
  format: 'pdf' | 'docx' | 'fountain' = 'pdf',
  fontFamily: string = 'Courier',
  fontSize: number = 12
) {
  const url = getExportUrl(projectId, format, fontFamily, fontSize);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', '');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


