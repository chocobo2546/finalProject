import React from 'react'

export default function DataTable({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Year</th>
            <th>Gear</th>
            <th>Mile</th>
            <th>Price</th>
            <th>URL</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${r.url || ''}-${i}`}>
              <td>{i + 1}</td>
              <td title={r.title || ''}>{r.title || '-'}</td>
              <td>{r.year ?? '-'}</td>
              <td>{r.gear ?? '-'}</td>
              <td>{r.mile ?? '-'}</td>
              <td>{r.price ?? '-'}</td>
              <td>
                {r.url ? (
                  <a href={r.url} target="_blank" rel="noreferrer">open</a>
                ) : (
                  '-'
                )}
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={7} className="muted" style={{ padding: 14 }}>
                No rows
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
