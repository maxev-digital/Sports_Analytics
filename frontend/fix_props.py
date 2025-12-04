#!/usr/bin/env python3
"""
Fix Props.tsx to:
1. Replace both old fetch endpoints with /api/ui/props-edges
2. Fix propTypes to use edgeProps?.props
3. Add PropTypeTabs import and rendering
"""

import re

file_path = "src/pages/Props.tsx"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add PropTypeTabs import after TierGate import
content = re.sub(
    r"(import { TierGate.*?} from '../components/TierGate';)",
    r"\1\nimport { PropTypeTabs } from '../components/PropTypeTabs';",
    content
)

# 2. Replace the "all" mode fetch with unified endpoint
old_all_fetch = r'''  // Fetch props data \(basic view\)
  useEffect\(\(\) => \{
    if \(viewMode !== 'all'\) return;

    const fetchProps = async \(\) => \{
      setLoading\(true\);
      try \{
        const response = await fetch\(`/api/props/\$\{selectedSport\}`\);
        if \(response\.ok\) \{
          const data = await response\.json\(\);
          setProps\(data\.props \|\| \[\]\);
        \}
      \} catch \(error\) \{
        console\.error\('Error fetching props:', error\);
      \} finally \{
        setLoading\(false\);
      \}
    \};

    fetchProps\(\);
    const interval = setInterval\(fetchProps, 60000\); // Refresh every minute

    return \(\) => clearInterval\(interval\);
  \}, \[selectedSport, viewMode\]\);'''

new_unified_fetch = r'''  // UNIFIED: Fetch props with edges from /api/ui/props-edges for ALL modes
  useEffect(() => {
    const fetchEdgeProps = async () => {
      setLoading(true);
      try {
        // Unified UI endpoint with all filters
        const params = new URLSearchParams({
          sport: selectedSport,
          min_edge: minEdge.toString(),
          view_mode: viewMode
        });

        const response = await fetch(getApiUrl(`ui/props-edges?${params.toString()}`));
        if (response.ok) {
          const data: MLPropsResponse = await response.json();
          setEdgeProps(data);
        }
      } catch (error) {
        console.error('Error fetching edge props:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEdgeProps();
    const interval = setInterval(fetchEdgeProps, 120000); // Refresh every 2 minutes

    return () => clearInterval(interval);
  }, [selectedSport, viewMode, minEdge]);'''

content = re.sub(old_all_fetch, new_unified_fetch, content, flags=re.DOTALL)

# 3. Remove the old "edges" mode fetch (lines 111-135)
old_edges_fetch = r'''  // Fetch advanced props with edges \(edges view\)
  useEffect\(\(\) => \{
    if \(viewMode !== 'edges'\) return;
    if \(selectedSport !== 'nba'\) return; // Only NBA supported for now

    const fetchEdgeProps = async \(\) => \{
      setLoading\(true\);
      try \{
        const response = await fetch\(`/api/player-props/nba/edges\?min_edge_pct=\$\{minEdge\}`\);
        if \(response\.ok\) \{
          const data: MLPropsResponse = await response\.json\(\);
          setEdgeProps\(data\);
        \}
      \} catch \(error\) \{
        console\.error\('Error fetching edge props:', error\);
      \} finally \{
        setLoading\(false\);
      \}
    \};

    fetchEdgeProps\(\);
    const interval = setInterval\(fetchEdgeProps, 120000\); // Refresh every 2 minutes \(slower since this is more expensive\)

    return \(\) => clearInterval\(interval\);
  \}, \[selectedSport, viewMode, minEdge\]\);'''

content = re.sub(old_edges_fetch, '', content, flags=re.DOTALL)

# 4. Fix propTypes to use edgeProps?.props
content = re.sub(
    r"const propTypes = Array\.from\(new Set\(props\.map\(p => p\.prop_type\)\)\);",
    r"const propTypes = Array.from(new Set((edgeProps?.props || []).map(p => p.prop_type)));",
    content
)

# 5. Add PropTypeTabs before "Props Table" in "all" mode (line ~611)
# Find the pattern and insert PropTypeTabs
pattern = r'(/\* RENDER: All Props View.*?\*/\s*<>\s*\{/\* Props Table \*/\})'
replacement = r'\1\n            {/* Prop Type Tabs */}\n            <PropTypeTabs \n              propTypes={propTypes}\n              selectedPropType={selectedPropType}\n              onSelectPropType={setSelectedPropType}\n              formatPropType={formatPropType}\n            />\n'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed Props.tsx successfully!")
print("Changes made:")
print("  1. Added PropTypeTabs import")
print("  2. Replaced both fetch endpoints with unified /api/ui/props-edges")
print("  3. Fixed propTypes to use edgeProps?.props")
print("  4. Added PropTypeTabs rendering")
