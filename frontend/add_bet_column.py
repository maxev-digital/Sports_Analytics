#!/usr/bin/env python3
"""
Add 'Bet' column to MaxEvEdges.tsx between Prediction and Edge columns
"""
import re

file_path = "src/pages/MaxEvEdges.tsx"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add table header for "Bet" column
header_pattern = r'''(<th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Model's predicted value">
                            <span className="cursor-help">Prediction</span>
                          </Tooltip>
                        </th>)
                        (<th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick=\{\(\) => toggleSort\('edge'\)\}>)'''

header_replacement = r'''\1
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Recommended bet based on model prediction">
                            <span className="cursor-help">Bet</span>
                          </Tooltip>
                        </th>
                        \2'''

content = re.sub(header_pattern, header_replacement, content, flags=re.DOTALL)

# Step 2: Add data cell for "Bet" column
cell_pattern = r'''(<td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-blue-400 font-semibold text-base">
                                \{play\.model_prediction\.toFixed\(1\)\}
                              </div>
                            </td>)
                            (<td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-green-400 font-bold text-lg">)'''

cell_replacement = r'''\1
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className={`font-bold text-base ${
                                play.recommendation === 'OVER' || play.recommendation === 'HOME' ? 'text-green-400' :
                                play.recommendation === 'UNDER' || play.recommendation === 'AWAY' ? 'text-red-400' :
                                'text-yellow-400'
                              }`}>
                                {play.recommendation}
                              </div>
                            </td>
                            \2'''

content = re.sub(cell_pattern, cell_replacement, content, flags=re.DOTALL)

# Step 3: Update colspan in empty state
content = content.replace(
    '<td colSpan={10}',
    '<td colSpan={11}'
)

# Step 4: Update column list in empty state message
content = content.replace(
    'Game | Sport | Bet Type | Line | Prediction | Edge | Confidence | Kelly % | Model | Consensus',
    'Game | Sport | Bet Type | Line | Prediction | Bet | Edge | Confidence | Kelly % | Model | Consensus'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('[SUCCESS] Added Bet column to MaxEvEdges.tsx')
print('  - Table header added between Prediction and Edge')
print('  - Data cell added with color coding:')
print('    - OVER/HOME: Green')
print('    - UNDER/AWAY: Red')
print('    - Other: Yellow')
print('  - Updated colspan and column list')
