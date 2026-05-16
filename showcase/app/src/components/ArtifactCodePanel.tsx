import Editor from '@monaco-editor/react';

export type SupportedLanguage = 'json' | 'markdown' | 'typescript' | 'plaintext';

interface ArtifactCodePanelProps {
  value: string;
  language?: SupportedLanguage;
  height?: string | number;
  readOnly?: boolean;
}

/**
 * A read-only Monaco editor panel for inspecting replay artifact content.
 * No filesystem access. No external API calls. Stable layout via explicit height.
 */
export function ArtifactCodePanel({
  value,
  language = 'json',
  height = '100%',
  readOnly = true
}: ArtifactCodePanelProps) {
  return (
    <Editor
      height={height}
      language={language}
      value={value}
      theme="vs-dark"
      options={{
        readOnly,
        minimap: { enabled: false },
        wordWrap: 'on',
        scrollBeyondLastLine: false,
        renderLineHighlight: 'none',
        overviewRulerLanes: 0,
        hideCursorInOverviewRuler: true,
        folding: true,
        fontSize: 13,
        lineNumbersMinChars: 3,
        padding: { top: 12, bottom: 12 }
      }}
      loading={
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#6b7280',
          fontSize: 13,
          fontFamily: 'monospace'
        }}>
          Loading editor…
        </div>
      }
    />
  );
}
