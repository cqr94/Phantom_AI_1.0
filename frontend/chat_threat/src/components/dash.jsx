import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box, Card, CardContent, Chip, Divider, Grid, IconButton,
  LinearProgress, Stack, Tab, Tabs, Tooltip, Typography,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Avatar, Paper, Select, MenuItem, FormControl, InputLabel,
  List, ListItem, ListItemText, Alert, AlertTitle, Collapse,
  TextField, InputAdornment, CircularProgress, Badge, Drawer,
  Accordion, AccordionSummary, AccordionDetails, Button
} from "@mui/material";
import { createTheme, ThemeProvider, alpha } from "@mui/material/styles";
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid,
  Tooltip as ReTooltip, LineChart, Line, ScatterChart, Scatter, ZAxis
} from "recharts";

// ─────────────────────────────────────────────────────────────
// API
// ─────────────────────────────────────────────────────────────
const BASE_URL = "http://localhost:8000";

async function apiFetch(path, params = {}) {
  try {
    const url = new URL(`${BASE_URL}${path}`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    const r = await fetch(url.toString());
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  } catch (e) {
    console.error(`[API] ${path}`, e);
    return null;
  }
}

function useThreatData() {
  const [data, setData] = useState({
    groups: [], techniques: [], campaigns: [], tactics: [],
    software: [], mitigations: [], stats: {}, timeline: [],
  });
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [groups, techniques, campaigns, tactics, software, mitigations, stats, timeline, healthData] =
        await Promise.all([
          apiFetch("/groups_neo4j"),
          apiFetch("/techniques"),
          apiFetch("/campaigns"),
          apiFetch("/tactics"),
          apiFetch("/software"),
          apiFetch("/mitigations"),
          apiFetch("/stats"),
          apiFetch("/timeline"),
          apiFetch("/health"),
        ]);
      setData({
        groups:      groups      || [],
        techniques:  techniques  || [],
        campaigns:   campaigns   || [],
        tactics:     tactics     || [],
        software:    software    || [],
        mitigations: mitigations || [],
        stats:       stats       || {},
        timeline:    timeline    || [],
      });
      setHealth(healthData);
      setLoading(false);
    }
    load();
  }, []);

  return { ...data, loading, health };
}

// ─────────────────────────────────────────────────────────────
// Theme — terminal green / deep navy
// ─────────────────────────────────────────────────────────────
const theme = createTheme({
  palette: {
    mode: "dark",
    primary:    { main: "#00FF9C" },
    secondary:  { main: "#4F8EF7" },
    error:      { main: "#FF4560" },
    warning:    { main: "#FFB800" },
    success:    { main: "#00FF9C" },
    info:       { main: "#4F8EF7" },
    background: { default: "#03080F", paper: "#070E18" },
    text:       { primary: "#C8D8EF", secondary: "#3D5470" },
  },
  typography: {
    fontFamily: "'IBM Plex Mono','Fira Code','Courier New',monospace",
    h4: { fontWeight: 800, letterSpacing: "-0.03em" },
    h5: { fontWeight: 700, letterSpacing: "-0.02em" },
    h6: { fontWeight: 600 },
    caption: { letterSpacing: "0.1em", textTransform: "uppercase", fontSize: "0.65rem" },
  },
  shape: { borderRadius: 4 },
  components: {
    MuiCard: { styleOverrides: { root: { backgroundImage: "none", border: "1px solid rgba(0,255,156,0.08)", backdropFilter: "blur(12px)", background: "#070E18" } } },
    MuiChip: { styleOverrides: { root: { fontSize: "0.63rem", height: 20, fontFamily: "inherit", borderRadius: 2 } } },
    MuiTableCell: {
      styleOverrides: {
        head: { color: "#3D5470", fontSize: "0.63rem", textTransform: "uppercase", letterSpacing: "0.1em", borderColor: "rgba(0,255,156,0.06)", background: "#070E18" },
        body: { fontSize: "0.77rem", borderColor: "rgba(0,255,156,0.04)", fontFamily: "'IBM Plex Mono','Fira Code',monospace" },
      },
    },
    MuiTab: { styleOverrides: { root: { fontSize: "0.7rem", textTransform: "none", fontFamily: "inherit", minHeight: 38, letterSpacing: "0.05em" } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiAccordion: { styleOverrides: { root: { backgroundImage: "none", background: "transparent" } } },
  },
});

// ─────────────────────────────────────────────────────────────
// SVG Icons
// ─────────────────────────────────────────────────────────────
const Icon = ({ d, size = 16, color = "currentColor", strokeWidth = 1.6 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const ICONS = {
  shield:     "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  threat:     "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  hunt:       "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  actor:      "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75",
  technique:  "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z",
  software:   "M20 7H4a2 2 0 00-2 2v6a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM12 17v4M8 21h8",
  mitigation: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
  graph:      "M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z",
  campaign:   "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17M17 17a2 2 0 100 4 2 2 0 000-4zM9 19a2 2 0 100 4 2 2 0 000-4z",
  tactic:     "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6-10l6-3m6 13l5.447-2.724A1 1 0 0021 16.382V5.618a1 1 0 00-.553-.894L15 2m0 18V7",
  search:     "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  link:       "M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71",
  close:      "M18 6L6 18M6 6l12 12",
  expand:     "M19 9l-7 7-7-7",
  timeline:   "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  globe:      "M12 2a10 10 0 100 20A10 10 0 0012 2zM2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z",
  alert:      "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
  chip:       "M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18",
};

// ─────────────────────────────────────────────────────────────
// Tactic palette
// ─────────────────────────────────────────────────────────────
const TACTIC_COLORS = {
  "Initial Access":       "#FF4560",
  "Execution":            "#FFB800",
  "Persistence":          "#7C3AED",
  "Privilege Escalation": "#EC4899",
  "Defense Evasion":      "#4F8EF7",
  "Credential Access":    "#8B5CF6",
  "Discovery":            "#00FF9C",
  "Lateral Movement":     "#F97316",
  "Collection":           "#06B6D4",
  "Command and Control":  "#FF4560",
  "Exfiltration":         "#FFB800",
  "Impact":               "#DC2626",
  "Reconnaissance":       "#6366F1",
  "Resource Development": "#14B8A6",
};
const tacticColor = (t) => TACTIC_COLORS[t] || "#3D5470";

// ─────────────────────────────────────────────────────────────
// Micro-components
// ─────────────────────────────────────────────────────────────
const MonoChip = ({ label, color = "#00FF9C", bg }) => (
  <Chip label={label} size="small" sx={{
    background: bg || alpha(color, 0.1),
    color,
    border: `1px solid ${alpha(color, 0.25)}`,
    fontSize: "0.62rem",
    height: 19,
    borderRadius: "2px",
  }} />
);

const StatusChip = ({ active }) => (
  <MonoChip
    label={active ? "ACTIVE" : "REVOKED"}
    color={active ? "#00FF9C" : "#3D5470"}
  />
);

const TacticChip = ({ tactic }) => {
  const c = tacticColor(tactic);
  return tactic
    ? <MonoChip label={tactic} color={c} />
    : null;
};

const ScanLine = () => (
  <Box sx={{
    position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
    pointerEvents: "none", overflow: "hidden", zIndex: 0, borderRadius: "inherit",
    "&::after": {
      content: '""',
      position: "absolute",
      left: 0, right: 0, height: "2px",
      background: "linear-gradient(90deg, transparent, rgba(0,255,156,0.08), transparent)",
      animation: "scanline 4s linear infinite",
    },
    "@keyframes scanline": {
      "0%":   { top: "0%" },
      "100%": { top: "100%" },
    },
  }} />
);

const StatCard = ({ icon, label, value, sub, color = "#00FF9C", blink }) => (
  <Card sx={{
    height: "100%",
    position: "relative",
    overflow: "hidden",
    background: `linear-gradient(135deg, #070E18 0%, ${alpha(color, 0.05)} 100%)`,
    borderColor: alpha(color, 0.15),
    transition: "border-color 0.3s",
    "&:hover": { borderColor: alpha(color, 0.4) },
  }}>
    <ScanLine />
    <CardContent sx={{ p: 1.75, position: "relative", zIndex: 1 }}>
      <Stack direction="row" alignItems="flex-start" justifyContent="space-between">
        <Box>
          <Typography variant="caption" sx={{ color: alpha(color, 0.6), letterSpacing: "0.12em" }}>{label}</Typography>
          <Typography variant="h4" sx={{
            color,
            mt: 0.4,
            fontWeight: 800,
            fontSize: { xs: "1.6rem", md: "2rem" },
            fontFamily: "'IBM Plex Mono',monospace",
            textShadow: `0 0 20px ${alpha(color, 0.4)}`,
            animation: blink ? "valuePulse 2s ease-in-out infinite" : "none",
            "@keyframes valuePulse": { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.7 } },
          }}>{value ?? "—"}</Typography>
          {sub && <Typography variant="caption" sx={{ color: alpha(color, 0.45), fontSize: "0.58rem" }}>{sub}</Typography>}
        </Box>
        <Box sx={{ p: 0.75, borderRadius: 1, background: alpha(color, 0.08), border: `1px solid ${alpha(color, 0.15)}`, color }}>
          <Icon d={ICONS[icon]} size={18} color={color} />
        </Box>
      </Stack>
    </CardContent>
  </Card>
);

// ─────────────────────────────────────────────────────────────
// Detail Drawer — shows full entity on click
// ─────────────────────────────────────────────────────────────
function EntityDrawer({ entity, entityType, onClose, techniques }) {
  const [rels, setRels] = useState(null);
  const [loadingRels, setLoadingRels] = useState(false);

  useEffect(() => {
    if (!entity?.id) return;
    setLoadingRels(true);
    apiFetch("/relationships", { node_id: entity.id, depth: 1 }).then(r => {
      setRels(r || []);
      setLoadingRels(false);
    });
  }, [entity?.id]);

  if (!entity) return null;

  const Field = ({ label, value }) => value ? (
    <Box mb={1}>
      <Typography variant="caption" sx={{ color: "#3D5470", display: "block" }}>{label}</Typography>
      <Typography variant="body2" sx={{ color: "#C8D8EF", fontSize: "0.78rem", lineHeight: 1.5 }}>{value}</Typography>
    </Box>
  ) : null;

  const ListField = ({ label, items, color = "#00FF9C" }) => items?.length > 0 ? (
    <Box mb={1}>
      <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 0.5 }}>{label}</Typography>
      <Stack direction="row" flexWrap="wrap" gap={0.5}>
        {items.slice(0, 20).map((item, i) => <MonoChip key={i} label={item} color={color} />)}
        {items.length > 20 && <Typography variant="caption" color="text.secondary">+{items.length - 20} more</Typography>}
      </Stack>
    </Box>
  ) : null;

  return (
    <Drawer anchor="right" open={!!entity} onClose={onClose}
      PaperProps={{ sx: { width: { xs: "100%", sm: 440 }, background: "#07111E", border: "none", borderLeft: "1px solid rgba(0,255,156,0.12)", p: 2.5, overflowX: "hidden" } }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={2}>
        <Stack spacing={0.5}>
          <MonoChip label={entityType?.toUpperCase()} color="#4F8EF7" />
          {entity.id && <MonoChip label={entity.id} color="#00FF9C" />}
        </Stack>
        <IconButton onClick={onClose} size="small" sx={{ color: "#3D5470", "&:hover": { color: "#00FF9C" } }}>
          <Icon d={ICONS.close} size={16} />
        </IconButton>
      </Stack>

      <Typography variant="h6" sx={{ color: "#E2E8F0", mb: 2, fontSize: "1rem", lineHeight: 1.3 }}>{entity.name}</Typography>

      <Divider sx={{ borderColor: "rgba(0,255,156,0.08)", mb: 2 }} />

      <Field label="Description" value={entity.description} />
      <Field label="Nation / Origin" value={entity.nation} />
      <Field label="URL" value={entity.url} />
      <Field label="Created" value={entity.created?.slice(0, 10)} />
      <Field label="Modified" value={entity.modified?.slice(0, 10)} />
      <Field label="First Seen" value={entity.firstSeen?.slice(0, 10) || entity.first_seen?.slice(0, 10)} />
      <Field label="Last Seen" value={entity.lastSeen?.slice(0, 10) || entity.last_seen?.slice(0, 10)} />
      <Field label="ATT&CK Version" value={entity.attack_version} />
      <Field label="Parent Technique" value={entity.parentId} />
      <Field label="Is Subtechnique" value={entity.isSubtechnique ? "Yes" : null} />

      <ListField label="Aliases" items={entity.aliases?.length ? entity.aliases : entity.alias ? [entity.alias] : []} />
      <ListField label="Platforms" items={entity.platforms} color="#4F8EF7" />
      <ListField label="Data Sources" items={entity.dataSources} color="#06B6D4" />
      <ListField label="Defense Bypass" items={entity.defenseBypass} color="#FF4560" />
      <ListField label="Tactics" items={entity.tacticNames || (entity.tactic ? [entity.tactic] : [])} color={tacticColor(entity.tactic)} />
      <ListField label="Techniques Used" items={entity.techniqueNames || entity.techniqueIds} color="#FFB800" />
      <ListField label="Groups Using" items={entity.groupNames || entity.groupIds} color="#4F8EF7" />
      <ListField label="Software Used" items={entity.softwareNames || entity.softwareIds} color="#F97316" />
      <ListField label="Campaigns" items={entity.campaignNames || entity.campaignIds} color="#FF4560" />
      <ListField label="Mitigations" items={entity.mitigationNames || entity.mitigationIds} color="#00FF9C" />
      <ListField label="Subtechniques" items={entity.subtechniqueIds} color="#8B5CF6" />
      <ListField label="Tactics Covered" items={entity.tacticsCovered} />

      {/* Relationships from /relationships */}
      {rels !== null && (
        <Box mt={2}>
          <Divider sx={{ borderColor: "rgba(0,255,156,0.08)", mb: 1.5 }} />
          <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>
            Graph Relationships {loadingRels ? "(loading…)" : `(${rels.length})`}
          </Typography>
          <Stack spacing={0.5} sx={{ maxHeight: 260, overflow: "auto" }}>
            {rels.slice(0, 30).map((r, i) => (
              <Box key={i} sx={{ p: 0.75, background: "rgba(79,142,247,0.04)", border: "1px solid rgba(79,142,247,0.08)", borderRadius: 1 }}>
                <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap" gap={0.3}>
                  <Typography variant="caption" sx={{ color: "#4F8EF7", fontSize: "0.6rem" }}>{r.sourceLabel}</Typography>
                  <Typography variant="caption" sx={{ color: "#3D5470" }}>→</Typography>
                  <Typography variant="caption" sx={{ color: "#FFB800", fontSize: "0.58rem" }}>{r.relationship}</Typography>
                  <Typography variant="caption" sx={{ color: "#3D5470" }}>→</Typography>
                  <Typography variant="caption" sx={{ color: "#00FF9C", fontSize: "0.6rem" }}>{r.targetLabel}</Typography>
                  <Typography variant="caption" sx={{ color: "#C8D8EF", fontSize: "0.62rem", ml: 0.5 }}>{r.targetName || r.targetId}</Typography>
                </Stack>
              </Box>
            ))}
            {rels.length > 30 && <Typography variant="caption" color="text.secondary">…and {rels.length - 30} more</Typography>}
          </Stack>
        </Box>
      )}
    </Drawer>
  );
}

// ─────────────────────────────────────────────────────────────
// Global Search Panel
// ─────────────────────────────────────────────────────────────
function GlobalSearch({ onSelect }) {
  const [q, setQ]           = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (q.length < 2) { setResults([]); return; }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      const r = await apiFetch("/search", { q, limit: 30 });
      setResults(r || []);
      setLoading(false);
    }, 350);
  }, [q]);

  const ENTITY_COLORS = {
    Group: "#4F8EF7", Technique: "#FFB800", Campaign: "#FF4560",
    Software: "#F97316", Mitigation: "#00FF9C", Tactic: "#06B6D4",
  };

  return (
    <Box sx={{ position: "relative", minWidth: 280 }}>
      <TextField
        size="small"
        placeholder="Search graph…"
        value={q}
        onChange={e => setQ(e.target.value)}
        InputProps={{
          startAdornment: <InputAdornment position="start">
            <Icon d={ICONS.search} size={13} color="#3D5470" />
          </InputAdornment>,
          endAdornment: loading ? <CircularProgress size={12} sx={{ color: "#00FF9C" }} /> : null,
          sx: { fontSize: "0.75rem", fontFamily: "inherit" },
        }}
        sx={{ "& .MuiOutlinedInput-root": { borderRadius: 1, borderColor: "rgba(0,255,156,0.15)", background: "#07111E" } }}
      />
      {results.length > 0 && (
        <Paper sx={{
          position: "absolute", top: "100%", left: 0, right: 0, zIndex: 99,
          mt: 0.5, maxHeight: 320, overflow: "auto",
          background: "#07111E", border: "1px solid rgba(0,255,156,0.15)",
          borderRadius: 1,
        }}>
          {results.map((r, i) => {
            const c = ENTITY_COLORS[r.entityType] || "#3D5470";
            return (
              <Box key={i} onClick={() => { onSelect(r, r.entityType); setQ(""); setResults([]); }}
                sx={{ px: 1.5, py: 0.75, cursor: "pointer", borderBottom: "1px solid rgba(0,255,156,0.04)",
                  "&:hover": { background: "rgba(0,255,156,0.04)" } }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <MonoChip label={r.entityType} color={c} />
                  <Box>
                    <Typography variant="caption" sx={{ color: "#C8D8EF", display: "block" }}>{r.name}</Typography>
                    {r.id && <Typography variant="caption" sx={{ color: "#3D5470", fontSize: "0.6rem" }}>{r.id}</Typography>}
                  </Box>
                </Stack>
              </Box>
            );
          })}
        </Paper>
      )}
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────
// Timeline chart (from /timeline)
// ─────────────────────────────────────────────────────────────
function TimelinePanel({ data }) {
  if (!data?.length) return (
    <Box sx={{ py: 3, textAlign: "center" }}>
      <Typography variant="caption" color="text.secondary">No timeline data in graph.</Typography>
    </Box>
  );

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="tlGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00FF9C" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#00FF9C" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,255,156,0.06)" />
        <XAxis dataKey="day" tick={{ fill: "#3D5470", fontSize: 9 }} axisLine={false} tickLine={false}
          tickFormatter={d => d?.slice(5)} interval="preserveStartEnd" />
        <YAxis tick={{ fill: "#3D5470", fontSize: 9 }} axisLine={false} tickLine={false} />
        <ReTooltip
          contentStyle={{ background: "#07111E", border: "1px solid rgba(0,255,156,0.2)", borderRadius: 4, fontSize: 11, fontFamily: "inherit" }}
          labelStyle={{ color: "#3D5470" }}
          itemStyle={{ color: "#00FF9C" }}
        />
        <Area type="monotone" dataKey="detections" stroke="#00FF9C" fill="url(#tlGrad)" strokeWidth={1.5} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ─────────────────────────────────────────────────────────────
// Main Dashboard
// ─────────────────────────────────────────────────────────────
export default function APTDashboard() {
  const [tab, setTab]             = useState(0);
  const [bannerOpen, setBannerOpen] = useState(true);
  const [searchQ, setSearchQ]     = useState("");
  const [tick, setTick]           = useState(0);
  const [selected, setSelected]   = useState(null);
  const [selectedType, setSelectedType] = useState(null);

  const { groups, techniques, campaigns, tactics, software, mitigations, stats, timeline, loading, health } =
    useThreatData();

  useEffect(() => {
    const t = setInterval(() => setTick(x => x + 1), 3000);
    return () => clearInterval(t);
  }, []);

  const openEntity = useCallback((entity, type) => {
    setSelected(entity);
    setSelectedType(type);
  }, []);

  const q = searchQ.toLowerCase();

  const filteredGroups = groups.filter(g =>
    !q || g.name?.toLowerCase().includes(q) || g.id?.toLowerCase().includes(q) ||
    g.nation?.toLowerCase().includes(q) || g.description?.toLowerCase().includes(q)
  );

  const filteredTechniques = techniques.filter(t =>
    !q || t.name?.toLowerCase().includes(q) || t.id?.toLowerCase().includes(q)
  );

  const topTechniques = [...techniques].sort((a, b) => b.groupCount - a.groupCount).slice(0, 14);

  const tacticBarData = tactics
    .filter(t => t.techniqueCount > 0)
    .sort((a, b) => b.techniqueCount - a.techniqueCount)
    .slice(0, 14)
    .map(t => ({
      name: (t.tactic || t.name || "?").replace("Command and Control", "C2").replace("Privilege Escalation", "Priv. Esc."),
      techniques: t.techniqueCount,
    }));

  const topGroupsForRadar = [...groups].sort((a, b) => b.techniqueCount - a.techniqueCount).slice(0, 3);
  const tacticNames = tactics.slice(0, 8).map(t => t.tactic || t.name);
  const radarColors = ["#00FF9C", "#4F8EF7", "#FF4560"];
  const radarData = tacticNames.map((tName, ti) =>
    topGroupsForRadar.reduce((acc, g, gi) => {
      acc[g.name] = Math.round(20 + (g.techniqueCount / (groups[0]?.techniqueCount || 1)) * 80 * Math.abs(Math.sin((ti + gi) * 1.1 + 0.5)));
      return acc;
    }, { tactic: tName?.split(" ").pop() || "?" })
  );

  const s = stats || {};
  const dbOk = health?.db !== false;

  const TABS = ["Threat Actors", "Techniques", "Campaigns", "Tactics", "Software", "Mitigations", "Timeline", "Schema"];

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{
        minHeight: "100vh",
        background: "#03080F",
        backgroundImage: "radial-gradient(ellipse at 20% 10%, rgba(0,255,156,0.03) 0%, transparent 60%), radial-gradient(ellipse at 80% 90%, rgba(79,142,247,0.03) 0%, transparent 60%)",
        p: { xs: 1, md: 1.5 },
        fontFamily: "'IBM Plex Mono',monospace",
      }}>

        {/* ─── Header ─── */}
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1.5} flexWrap="wrap" gap={1}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Box sx={{
              p: 0.75, borderRadius: 1,
              background: "rgba(0,255,156,0.07)",
              border: "1px solid rgba(0,255,156,0.2)",
              boxShadow: "0 0 20px rgba(0,255,156,0.1)",
            }}>
              <Icon d={ICONS.shield} size={20} color="#00FF9C" />
            </Box>
            <Box>
              <Typography variant="h5" sx={{ color: "#E2E8F0", lineHeight: 1, fontSize: "1.05rem" }}>
                APT<Box component="span" sx={{ color: "#00FF9C" }}>·</Box>HUNT
              </Typography>
              <Typography variant="caption" sx={{ color: "#3D5470", fontSize: "0.58rem" }}>
                MITRE ATT&amp;CK · Neo4j · {s.relationships?.toLocaleString() || "—"} edges
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" gap={0.5}>
            <GlobalSearch onSelect={openEntity} />
            <Chip
              label={loading ? "SYNCING" : dbOk ? "LIVE" : "DB ERROR"}
              size="small"
              icon={<Box sx={{
                width: 5, height: 5, borderRadius: "50%",
                background: loading ? "#FFB800" : dbOk ? "#00FF9C" : "#FF4560",
                ml: "4px !important",
                boxShadow: `0 0 6px ${loading ? "#FFB800" : dbOk ? "#00FF9C" : "#FF4560"}`,
                animation: "dot 1.5s ease-in-out infinite",
                "@keyframes dot": { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.4 } },
              }} />}
              sx={{
                background: "rgba(0,255,156,0.06)",
                border: "1px solid rgba(0,255,156,0.2)",
                color: "#00FF9C",
                fontSize: "0.6rem",
                height: 24,
                "& .MuiChip-icon": { ml: 0 },
              }}
            />
            {s.highSeverityAlerts > 0 && (
              <Chip
                label={`${s.highSeverityAlerts} HIGH`}
                size="small"
                icon={<Icon d={ICONS.alert} size={11} color="#FF4560" />}
                sx={{ background: "rgba(255,69,96,0.08)", border: "1px solid rgba(255,69,96,0.25)", color: "#FF4560", fontSize: "0.6rem", height: 24 }}
              />
            )}
          </Stack>
        </Stack>

        {/* ─── Loading ─── */}
        {loading && (
          <Box sx={{ py: 8, display: "flex", justifyContent: "center" }}>
            <Stack alignItems="center" spacing={1.5}>
              <Box sx={{
                width: 48, height: 48, border: "2px solid rgba(0,255,156,0.15)",
                borderTop: "2px solid #00FF9C", borderRadius: "50%",
                animation: "spin 1s linear infinite",
                "@keyframes spin": { to: { transform: "rotate(360deg)" } },
              }} />
              <Typography variant="caption" sx={{ color: "#3D5470", letterSpacing: "0.2em" }}>
                QUERYING NEO4J…
              </Typography>
            </Stack>
          </Box>
        )}

        {!loading && <>

          {/* ─── Banner ─── */}
          <Collapse in={bannerOpen}>
            <Alert
              onClose={() => setBannerOpen(false)}
              severity="success"
              icon={<Icon d={ICONS.graph} size={16} color="#00FF9C" />}
              sx={{
                mb: 1.5,
                background: "rgba(0,255,156,0.04)",
                border: "1px solid rgba(0,255,156,0.15)",
                "& .MuiAlert-icon": { color: "#00FF9C", pt: "6px" },
                "& .MuiAlert-message": { width: "100%" },
              }}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1} flexWrap="wrap">
                {[
                  [s.groups, "Groups"],
                  [s.techniques, "Techniques"],
                  [s.campaigns, "Campaigns"],
                  [s.software, "Software"],
                  [s.mitigations, "Mitigations"],
                  [s.tactics, "Tactics"],
                  [s.alerts, "Alerts"],
                  [s.relationships, "Edges"],
                ].map(([v, label]) => v > 0 && (
                  <Chip key={label} label={`${v?.toLocaleString()} ${label}`} size="small"
                    sx={{ background: "rgba(0,255,156,0.08)", color: "#00FF9C", border: "1px solid rgba(0,255,156,0.15)", height: 18, fontSize: "0.6rem" }} />
                ))}
              </Stack>
            </Alert>
          </Collapse>

          {/* ─── Stat Cards ─── */}
          <Grid container spacing={1} mb={1.5}>
            {[
              { icon: "actor",      label: "Groups",      value: s.groups?.toLocaleString()      || groups.length,      sub: "tracked APTs",     color: "#4F8EF7" },
              { icon: "technique",  label: "Techniques",  value: s.techniques?.toLocaleString()  || techniques.length,  sub: "inc. sub-techs",   color: "#FFB800" },
              { icon: "campaign",   label: "Campaigns",   value: s.campaigns?.toLocaleString()   || campaigns.length,   sub: "attributed ops",   color: "#FF4560" },
              { icon: "software",   label: "Software",    value: s.software?.toLocaleString()    || software.length,    sub: "malware & tools",  color: "#F97316" },
              { icon: "mitigation", label: "Mitigations", value: s.mitigations?.toLocaleString() || mitigations.length, sub: "MITRE defences",   color: "#00FF9C" },
              { icon: "tactic",     label: "Tactics",     value: s.tactics?.toLocaleString()     || tactics.length,     sub: "kill-chain phases", color: "#06B6D4" },
            ].map((sc, i) => (
              <Grid item xs={6} sm={4} md={2} key={i}>
                <StatCard {...sc} />
              </Grid>
            ))}
          </Grid>

          {/* ─── Tabs ─── */}
          <Card sx={{ mb: 1.5 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}
              variant="scrollable" scrollButtons="auto"
              sx={{
                borderBottom: "1px solid rgba(0,255,156,0.08)",
                minHeight: 38,
                px: 1,
                "& .MuiTab-root": { color: "#3D5470", py: 0 },
                "& .MuiTab-root.Mui-selected": { color: "#00FF9C" },
                "& .MuiTabs-indicator": { background: "#00FF9C", height: 1 },
              }}>
              {TABS.map((label, i) => <Tab key={i} label={label} />)}
            </Tabs>

            {/* ══ Tab 0: Threat Actors ══ */}
            {tab === 0 && (
              <CardContent sx={{ p: 1.5 }}>
                <Stack direction="row" spacing={1} mb={1.5}>
                  <TextField size="small" placeholder="Filter by name, ID, nation…" value={searchQ}
                    onChange={e => setSearchQ(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start"><Icon d={ICONS.hunt} size={13} color="#3D5470" /></InputAdornment>, sx: { fontSize: "0.75rem", fontFamily: "inherit" } }}
                    sx={{ minWidth: 260 }} />
                  <Typography variant="caption" sx={{ color: "#3D5470", alignSelf: "center" }}>
                    {filteredGroups.length} / {groups.length}
                  </Typography>
                </Stack>
                <TableContainer sx={{ maxHeight: 420 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        {["ID", "Name", "Nation", "Techniques", "Software", "Campaigns", "First Seen", "Last Seen", "Status"].map(h => (
                          <TableCell key={h}>{h}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredGroups.slice(0, 60).map(g => (
                        <TableRow key={g.id} hover onClick={() => openEntity(g, "Group")}
                          sx={{ cursor: "pointer", "&:hover td": { background: "rgba(0,255,156,0.03)" } }}>
                          <TableCell><MonoChip label={g.id} color="#4F8EF7" /></TableCell>
                          <TableCell>
                            <Tooltip title={g.description?.slice(0, 220) || ""} placement="right" arrow>
                              <Typography variant="body2" fontWeight={600} color="#C8D8EF"
                                sx={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {g.name}
                              </Typography>
                            </Tooltip>
                            {g.aliases?.length > 0 && (
                              <Typography variant="caption" sx={{ color: "#3D5470", fontSize: "0.58rem" }}>
                                {g.aliases.slice(0, 2).join(", ")}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {g.nation ? <MonoChip label={g.nation} color="#06B6D4" /> : <Typography variant="caption" color="text.secondary">—</Typography>}
                          </TableCell>
                          <TableCell>
                            <Stack spacing={0.3}>
                              <Typography variant="caption" color="#FFB800">{g.techniqueCount}</Typography>
                              <LinearProgress variant="determinate" value={Math.min((g.techniqueCount / 120) * 100, 100)}
                                sx={{ height: 2, borderRadius: 1, background: "rgba(255,184,0,0.1)", "& .MuiLinearProgress-bar": { background: "#FFB800" } }} />
                            </Stack>
                          </TableCell>
                          <TableCell><Typography variant="caption">{g.softwareCount}</Typography></TableCell>
                          <TableCell><Typography variant="caption">{g.campaignCount}</Typography></TableCell>
                          <TableCell><Typography variant="caption" color="text.secondary">{g.firstSeen?.slice(0, 10) || "—"}</Typography></TableCell>
                          <TableCell><Typography variant="caption" color="text.secondary">{g.lastSeen?.slice(0, 10) || "—"}</Typography></TableCell>
                          <TableCell><StatusChip active={g.active !== false} /></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {filteredGroups.length > 60 && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                    Showing 60 of {filteredGroups.length} — use search to filter
                  </Typography>
                )}
              </CardContent>
            )}

            {/* ══ Tab 1: Techniques ══ */}
            {tab === 1 && (
              <CardContent sx={{ p: 1.5 }}>
                <Stack direction="row" spacing={1} mb={1.5}>
                  <TextField size="small" placeholder="Filter techniques…" value={searchQ}
                    onChange={e => setSearchQ(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start"><Icon d={ICONS.hunt} size={13} color="#3D5470" /></InputAdornment>, sx: { fontSize: "0.75rem", fontFamily: "inherit" } }}
                    sx={{ minWidth: 240 }} />
                </Stack>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Top by Group Usage</Typography>
                    <Box height={360}>
                      <ResponsiveContainer width="100%" height={360}>
                        <BarChart data={topTechniques} layout="vertical" margin={{ left: 8, right: 16 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,255,156,0.05)" horizontal={false} />
                          <XAxis type="number" tick={{ fill: "#3D5470", fontSize: 9 }} axisLine={false} tickLine={false} />
                          <YAxis type="category" dataKey="id" tick={{ fill: "#FFB800", fontSize: 9, fontFamily: "inherit" }}
                            axisLine={false} tickLine={false} width={70} />
                          <ReTooltip
                            contentStyle={{ background: "#07111E", border: "1px solid rgba(0,255,156,0.15)", borderRadius: 4, fontSize: 11, fontFamily: "inherit" }}
                            formatter={(v, _, p) => [v, "groups using " + (topTechniques.find(t => t.id === p.payload.id)?.name || "")]}
                          />
                          <Bar dataKey="groupCount" fill="#00FF9C" radius={[0, 3, 3, 0]} opacity={0.8} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Technique List</Typography>
                    <TableContainer sx={{ maxHeight: 380 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            {["ID", "Name", "Tactic", "Groups", "Sub?"].map(h => <TableCell key={h}>{h}</TableCell>)}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {filteredTechniques.slice(0, 80).map(t => (
                            <TableRow key={t.id} hover onClick={() => openEntity(t, "Technique")}
                              sx={{ cursor: "pointer", "&:hover td": { background: "rgba(0,255,156,0.03)" } }}>
                              <TableCell><MonoChip label={t.id} color="#FFB800" /></TableCell>
                              <TableCell>
                                <Typography variant="caption" color="#C8D8EF" fontWeight={500}
                                  sx={{ maxWidth: 160, display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                  {t.name}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                {t.tactic && <TacticChip tactic={t.tactic} />}
                              </TableCell>
                              <TableCell><Typography variant="caption" color="#00FF9C">{t.groupCount}</Typography></TableCell>
                              <TableCell>
                                {t.isSubtechnique && <MonoChip label="SUB" color="#8B5CF6" />}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                </Grid>
              </CardContent>
            )}

            {/* ══ Tab 2: Campaigns ══ */}
            {tab === 2 && (
              <CardContent sx={{ p: 1.5 }}>
                {campaigns.length === 0 ? (
                  <Typography variant="caption" color="text.secondary">No campaigns in graph.</Typography>
                ) : (
                  <Grid container spacing={1}>
                    {campaigns.slice(0, 24).map(c => (
                      <Grid item xs={12} sm={6} md={4} key={c.id}>
                        <Paper onClick={() => openEntity(c, "Campaign")} sx={{
                          p: 1.5, height: "100%",
                          background: "rgba(255,69,96,0.03)",
                          border: "1px solid rgba(255,69,96,0.1)",
                          cursor: "pointer",
                          transition: "all 0.2s",
                          "&:hover": { borderColor: "rgba(255,69,96,0.35)", transform: "translateY(-2px)", background: "rgba(255,69,96,0.05)" },
                        }}>
                          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                            <MonoChip label={c.id} color="#FF4560" />
                            <StatusChip active={!c.revoked} />
                          </Stack>
                          <Typography variant="body2" fontWeight={700} color="#E2E8F0" mb={1}
                            sx={{ fontSize: "0.8rem", lineHeight: 1.3 }}>{c.name}</Typography>
                          {[
                            ["Groups",     c.groupNames?.slice(0, 2).join(", ") || c.groupIds?.length || "—"],
                            ["First seen", c.firstSeen?.slice(0, 10) || "—"],
                            ["Last seen",  c.lastSeen?.slice(0, 10)  || "—"],
                            ["Techniques", c.techniqueCount],
                            ["Software",   c.softwareCount],
                          ].map(([k, v]) => (
                            <Stack key={k} direction="row" justifyContent="space-between" mb={0.3}>
                              <Typography variant="caption" color="text.secondary">{k}</Typography>
                              <Typography variant="caption" color={k === "Techniques" ? "#FFB800" : "#C8D8EF"} sx={{ maxWidth: 140, textAlign: "right", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {v}
                              </Typography>
                            </Stack>
                          ))}
                          <LinearProgress variant="determinate" value={Math.min((c.techniqueCount || 0) * 3, 100)}
                            sx={{ mt: 1, height: 2, borderRadius: 1, background: "rgba(255,69,96,0.1)", "& .MuiLinearProgress-bar": { background: "#FF4560" } }} />
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </CardContent>
            )}

            {/* ══ Tab 3: Tactics ══ */}
            {tab === 3 && (
              <CardContent sx={{ p: 1.5 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={8}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Techniques per Tactic</Typography>
                    <Box height={300}>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={tacticBarData} margin={{ top: 4, right: 4, left: -20, bottom: 48 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,255,156,0.05)" />
                          <XAxis dataKey="name" tick={{ fill: "#3D5470", fontSize: 9 }} angle={-40} textAnchor="end" axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: "#3D5470", fontSize: 9 }} axisLine={false} tickLine={false} />
                          <ReTooltip contentStyle={{ background: "#07111E", border: "1px solid rgba(0,255,156,0.15)", borderRadius: 4, fontSize: 11, fontFamily: "inherit" }} />
                          <Bar dataKey="techniques" fill="#00FF9C" radius={[3, 3, 0, 0]} opacity={0.8} name="Techniques" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Kill-chain Coverage</Typography>
                    <Stack spacing={0.75} sx={{ maxHeight: 360, overflow: "auto" }}>
                      {tactics.map((t, i) => {
                        const c = tacticColor(t.tactic || t.name);
                        return (
                          <Box key={i} onClick={() => openEntity(t, "Tactic")} sx={{ cursor: "pointer", "&:hover": { opacity: 0.85 } }}>
                            <Stack direction="row" justifyContent="space-between" mb={0.3}>
                              <Typography variant="caption" color="#C8D8EF" noWrap sx={{ maxWidth: 170 }}>{t.tactic || t.name}</Typography>
                              <Typography variant="caption" fontWeight={700} sx={{ color: c, flexShrink: 0 }}>{t.techniqueCount}</Typography>
                            </Stack>
                            <LinearProgress variant="determinate" value={t.score || Math.min(t.techniqueCount * 4, 100)}
                              sx={{ height: 3, borderRadius: 1, background: "rgba(255,255,255,0.04)", "& .MuiLinearProgress-bar": { background: c, borderRadius: 1 } }} />
                          </Box>
                        );
                      })}
                    </Stack>
                  </Grid>
                </Grid>
              </CardContent>
            )}

            {/* ══ Tab 4: Software ══ */}
            {tab === 4 && (
              <CardContent sx={{ p: 1.5 }}>
                <TableContainer sx={{ maxHeight: 420 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        {["ID", "Name", "Type", "Groups", "Techniques", "Campaigns", "Platforms", "Status"].map(h => (
                          <TableCell key={h}>{h}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {[...software].sort((a, b) => b.groupCount - a.groupCount).slice(0, 80).map(sw => (
                        <TableRow key={sw.id} hover onClick={() => openEntity(sw, "Software")}
                          sx={{ cursor: "pointer", "&:hover td": { background: "rgba(249,115,22,0.03)" } }}>
                          <TableCell><MonoChip label={sw.id} color="#F97316" /></TableCell>
                          <TableCell>
                            <Tooltip title={sw.description?.slice(0, 220) || ""} placement="right" arrow>
                              <Typography variant="body2" fontWeight={600} color="#C8D8EF"
                                sx={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {sw.name}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            {sw.type && <MonoChip label={sw.type} color="#8B5CF6" />}
                          </TableCell>
                          <TableCell>
                            <Stack spacing={0.3}>
                              <Typography variant="caption" color="#F97316">{sw.groupCount}</Typography>
                              <LinearProgress variant="determinate" value={Math.min((sw.groupCount || 0) * 6, 100)}
                                sx={{ height: 2, borderRadius: 1, background: "rgba(249,115,22,0.1)", "& .MuiLinearProgress-bar": { background: "#F97316" } }} />
                            </Stack>
                          </TableCell>
                          <TableCell><Typography variant="caption">{sw.techniqueCount}</Typography></TableCell>
                          <TableCell><Typography variant="caption">{sw.campaignCount}</Typography></TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={0.3} flexWrap="wrap" gap={0.2}>
                              {sw.platforms?.slice(0, 2).map((p, i) => <MonoChip key={i} label={p} color="#06B6D4" />)}
                              {sw.platforms?.length > 2 && <Typography variant="caption" color="text.secondary">+{sw.platforms.length - 2}</Typography>}
                            </Stack>
                          </TableCell>
                          <TableCell><StatusChip active={!sw.revoked && !sw.deprecated} /></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            )}

            {/* ══ Tab 5: Mitigations ══ */}
            {tab === 5 && (
              <CardContent sx={{ p: 1.5 }}>
                <TableContainer sx={{ maxHeight: 420 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        {["ID", "Name", "Techniques Covered", "Tactics Covered", "Modified"].map(h => (
                          <TableCell key={h}>{h}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {[...mitigations].sort((a, b) => b.techniqueCount - a.techniqueCount).map(m => (
                        <TableRow key={m.id} hover onClick={() => openEntity(m, "Mitigation")}
                          sx={{ cursor: "pointer", "&:hover td": { background: "rgba(0,255,156,0.03)" } }}>
                          <TableCell><MonoChip label={m.id} color="#00FF9C" /></TableCell>
                          <TableCell>
                            <Tooltip title={m.description?.slice(0, 220) || ""} placement="right" arrow>
                              <Typography variant="body2" fontWeight={600} color="#C8D8EF"
                                sx={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {m.name}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Stack spacing={0.3}>
                              <Typography variant="caption" color="#00FF9C">{m.techniqueCount}</Typography>
                              <LinearProgress variant="determinate" value={Math.min((m.techniqueCount / 50) * 100, 100)}
                                sx={{ height: 2, borderRadius: 1, background: "rgba(0,255,156,0.08)", "& .MuiLinearProgress-bar": { background: "#00FF9C" } }} />
                            </Stack>
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={0.3} flexWrap="wrap" gap={0.2}>
                              {m.tacticsCovered?.slice(0, 3).map((t, i) => <TacticChip key={i} tactic={t} />)}
                              {m.tacticsCovered?.length > 3 && <Typography variant="caption" color="text.secondary">+{m.tacticsCovered.length - 3}</Typography>}
                            </Stack>
                          </TableCell>
                          <TableCell><Typography variant="caption" color="text.secondary">{m.modified?.slice(0, 10) || "—"}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            )}

            {/* ══ Tab 6: Timeline ══ */}
            {tab === 6 && (
              <CardContent sx={{ p: 1.5 }}>
                <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1.5 }}>
                  Detection / Alert Activity Over Time
                </Typography>
                <TimelinePanel data={timeline} />
                {timeline.length > 0 && (
                  <Box mt={2}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>
                      Recent Days
                    </Typography>
                    <TableContainer sx={{ maxHeight: 240 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            {["Date", "Detections", "Severity Mix", "Techniques"].map(h => <TableCell key={h}>{h}</TableCell>)}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {[...timeline].reverse().slice(0, 30).map((row, i) => (
                            <TableRow key={i} hover>
                              <TableCell><Typography variant="caption" color="#4F8EF7">{row.day}</Typography></TableCell>
                              <TableCell><Typography variant="caption" color="#00FF9C" fontWeight={700}>{row.detections}</Typography></TableCell>
                              <TableCell>
                                <Stack direction="row" gap={0.3} flexWrap="wrap">
                                  {row.severities?.map((sev, j) => (
                                    <MonoChip key={j} label={sev}
                                      color={sev === "CRITICAL" ? "#FF4560" : sev === "HIGH" ? "#FFB800" : sev === "MEDIUM" ? "#F97316" : "#3D5470"} />
                                  ))}
                                </Stack>
                              </TableCell>
                              <TableCell>
                                <Typography variant="caption" color="text.secondary">
                                  {row.techniqueIds?.slice(0, 3).join(", ")}{row.techniqueIds?.length > 3 ? "…" : ""}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
              </CardContent>
            )}

            {/* ══ Tab 7: Schema ══ */}
            {tab === 7 && (
              <CardContent sx={{ p: 1.5 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Node Labels</Typography>
                    <Stack spacing={0.5}>
                      {[
                        ["MitreAttackGroup",        "#4F8EF7",  s.groups],
                        ["MitreAttackTechnique",     "#FFB800",  s.techniques],
                        ["MitreAttackTactic",        "#00FF9C",  s.tactics],
                        ["MitreAttackSoftware",      "#F97316",  s.software],
                        ["MitreAttackCampaign",      "#FF4560",  s.campaigns],
                        ["MitreAttackMitigation",    "#06B6D4",  s.mitigations],
                        ["Alert",                    "#8B5CF6",  s.alerts],
                        ["Detection",                "#EC4899",  s.detections],
                      ].map(([label, color, count]) => (
                        <Stack key={label} direction="row" alignItems="center" spacing={1}
                          sx={{ p: 0.75, background: "rgba(0,255,156,0.02)", border: "1px solid rgba(0,255,156,0.06)", borderRadius: 1 }}>
                          <Box sx={{ width: 6, height: 6, borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}`, flexShrink: 0 }} />
                          <Typography variant="caption" color="#C8D8EF" flex={1} sx={{ fontSize: "0.68rem" }}>{label}</Typography>
                          <Typography variant="caption" sx={{ color, fontWeight: 700, fontSize: "0.68rem" }}>
                            {count?.toLocaleString() ?? "—"}
                          </Typography>
                        </Stack>
                      ))}
                    </Stack>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>Relationship Types</Typography>
                    <Stack spacing={0.4}>
                      {[
                        "MITRE_ATTACK_GROUP_USES_TECHNIQUE",
                        "MITRE_ATTACK_GROUP_USES_SOFTWARE",
                        "MITRE_ATTACK_MITIGATION_DEFENDS_AGAINST_TECHNIQUE",
                        "MITRE_CAMPAIGN_USES_SOFTWARE",
                        "MITRE_CAMPAIGN_USES_TECHNIQUE",
                        "MITRE_MATRIX_INCLUDES_TACTIC",
                        "MITRE_SOFTWARE_USES_TECHNIQUE",
                        "MITRE_SUBTECHNIQUE_OF",
                        "MITRE_TACTIC_INCLUDES_TECHNIQUE",
                      ].map(rel => (
                        <Box key={rel} sx={{ px: 1, py: 0.5, background: "rgba(79,142,247,0.04)", border: "1px solid rgba(79,142,247,0.1)", borderRadius: 1 }}>
                          <Typography sx={{ color: "#4F8EF7", fontSize: "0.62rem", letterSpacing: "0.02em", fontFamily: "inherit" }}>{rel}</Typography>
                        </Box>
                      ))}
                      <Box sx={{ px: 1, py: 0.5, background: "rgba(0,255,156,0.03)", border: "1px solid rgba(0,255,156,0.1)", borderRadius: 1 }}>
                        <Typography sx={{ color: "#3D5470", fontSize: "0.62rem" }}>Total edges: {s.relationships?.toLocaleString() || "—"}</Typography>
                      </Box>
                    </Stack>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>API Endpoints</Typography>
                    <Stack spacing={0.4}>
                      {[
                        ["/groups_neo4j",   "#4F8EF7",  "Groups + relationship lists"],
                        ["/techniques",      "#FFB800",  "Techniques + subtechs + tactics"],
                        ["/campaigns",       "#FF4560",  "Campaigns + groups + software"],
                        ["/tactics",         "#00FF9C",  "Tactics + technique counts"],
                        ["/software",        "#F97316",  "Software + platforms + aliases"],
                        ["/mitigations",     "#06B6D4",  "Mitigations + tactics covered"],
                        ["/alerts",          "#8B5CF6",  "Alerts with full context"],
                        ["/timeline",        "#EC4899",  "Detection events over time"],
                        ["/stats",           "#C8D8EF",  "Node/edge/severity counts"],
                        ["/search?q=…",      "#00FF9C",  "Cross-entity search"],
                        ["/relationships",   "#4F8EF7",  "Graph traversal by node ID"],
                        ["/health",          "#00FF9C",  "DB connectivity check"],
                      ].map(([path, color, desc]) => (
                        <Box key={path} sx={{ px: 1, py: 0.5, background: "rgba(0,255,156,0.02)", border: "1px solid rgba(0,255,156,0.06)", borderRadius: 1 }}>
                          <Typography sx={{ color, fontSize: "0.63rem", fontFamily: "inherit" }}>{path}</Typography>
                          <Typography sx={{ color: "#3D5470", fontSize: "0.58rem" }}>{desc}</Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Grid>
                </Grid>
              </CardContent>
            )}
          </Card>

          {/* ─── Bottom Row: Radar + Mitigations ─── */}
          <Grid container spacing={1.5}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent sx={{ p: 1.5 }}>
                  <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>
                    Top Groups — Tactic Coverage Radar
                  </Typography>
                  <Box height={240}>
                    <ResponsiveContainer width="100%" height={240}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="rgba(0,255,156,0.1)" />
                        <PolarAngleAxis dataKey="tactic" tick={{ fill: "#3D5470", fontSize: 9, fontFamily: "inherit" }} />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#3D5470", fontSize: 8 }} axisLine={false} />
                        {topGroupsForRadar.map((g, i) => (
                          <Radar key={g.id} name={g.name} dataKey={g.name}
                            stroke={radarColors[i]} fill={radarColors[i]}
                            fillOpacity={0.08} strokeWidth={1.5} />
                        ))}
                        <ReTooltip contentStyle={{ background: "#07111E", border: "1px solid rgba(0,255,156,0.15)", borderRadius: 4, fontSize: 11, fontFamily: "inherit" }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </Box>
                  <Stack direction="row" spacing={2} justifyContent="center" mt={0.5} flexWrap="wrap" gap={0.5}>
                    {topGroupsForRadar.map((g, i) => (
                      <Stack key={g.id} direction="row" spacing={0.5} alignItems="center">
                        <Box sx={{ width: 8, height: 8, borderRadius: 1, background: radarColors[i], boxShadow: `0 0 5px ${radarColors[i]}` }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>{g.name}</Typography>
                      </Stack>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent sx={{ p: 1.5 }}>
                  <Typography variant="caption" sx={{ color: "#3D5470", display: "block", mb: 1 }}>
                    Top Mitigations by Coverage
                  </Typography>
                  <Stack spacing={0.5} sx={{ maxHeight: 265, overflow: "auto" }}>
                    {[...mitigations].sort((a, b) => b.techniqueCount - a.techniqueCount).slice(0, 14).map(m => (
                      <Box key={m.id} onClick={() => openEntity(m, "Mitigation")}
                        sx={{ px: 1.25, py: 0.75, background: "rgba(6,182,212,0.03)", border: "1px solid rgba(6,182,212,0.08)", borderRadius: 1, cursor: "pointer", "&:hover": { borderColor: "rgba(6,182,212,0.25)" } }}>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <MonoChip label={m.id} color="#06B6D4" />
                          <Typography variant="caption" flex={1} color="#C8D8EF" noWrap>{m.name}</Typography>
                          <Stack alignItems="flex-end" sx={{ flexShrink: 0 }}>
                            <Typography variant="caption" color="#06B6D4" fontWeight={700}>{m.techniqueCount}</Typography>
                            <Typography sx={{ fontSize: "0.55rem", color: "#3D5470" }}>techniques</Typography>
                          </Stack>
                        </Stack>
                      </Box>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* ─── Footer ─── */}
          <Stack direction="row" justifyContent="space-between" mt={1.5} px={0.5} flexWrap="wrap" gap={0.5}>
            <Typography variant="caption" sx={{ color: "#3D5470", fontSize: "0.58rem" }}>
              APT·HUNT · MITRE ATT&amp;CK · Neo4j ·{" "}
              {s.groups} groups · {s.techniques} techniques · {s.relationships?.toLocaleString()} edges
            </Typography>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Typography variant="caption" sx={{ color: "#3D5470", fontSize: "0.58rem" }}>
                T+{tick * 3}s · TLP:RED
              </Typography>
              <Chip label={dbOk ? "DB OK" : "DB ERR"} size="small"
                sx={{ height: 16, fontSize: "0.55rem", background: dbOk ? "rgba(0,255,156,0.06)" : "rgba(255,69,96,0.1)", color: dbOk ? "#00FF9C" : "#FF4560", border: `1px solid ${dbOk ? "rgba(0,255,156,0.15)" : "rgba(255,69,96,0.2)"}` }} />
            </Stack>
          </Stack>
        </>}
      </Box>

      {/* ─── Entity Drawer ─── */}
      <EntityDrawer
        entity={selected}
        entityType={selectedType}
        onClose={() => setSelected(null)}
        techniques={techniques}
      />
    </ThemeProvider>
  );
}