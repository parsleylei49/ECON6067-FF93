import React from 'react';
import {EvidenceChart, DataComponent, DataTable, ReportSection, RichNarrative, useDataApp} from '../../data-app-public.jsx';

const previews={
  'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html':{
    title:'Kenneth French: three-factor definitions',summary:'Defines market, size and value factor construction. Numerical comparisons here use the supplied fixed-vintage series.',source:'Kenneth French Data Library',approvedForReport:true},
  'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html':{
    title:'Data Library construction notes',summary:'Documents changes to CRSP format and construction conventions relevant to the original-paper versus modern-benchmark comparison.',source:'Kenneth French Data Library',approvedForReport:true}
};
const chartTitles={market:'MKT−RF · January 2000–December 2025',smb:'SMB · July 2002–December 2025',hml:'HML · July 2002–December 2025','micro-smb':'SMB · exclude microcaps, fixed breakpoints','micro-hml':'HML · exclude microcaps, fixed breakpoints'};

function NarrativeParts({section,snapshot}) {
  const parts=section.text.split(/(\|[^\n]+\|\n\|[\s\S]*?)(?=\n\n|$)/g).filter(Boolean);
  let tableIndex=0;
  return parts.map((part,index)=>{
    if (!part.startsWith('|')) return <RichNarrative key={index} id={section.id+':prose-'+index} value={part.trim()} sourcePreviews={previews} label={'Edit '+section.title} />;
    const lines=part.trim().split('\n').map(x=>x.split('|').slice(1,-1).map(y=>y.trim()));
    const columns=lines[0].map((label,i)=>({field:'c'+i,label}));
    const rows=lines.slice(2).map(values=>Object.fromEntries(values.map((v,i)=>['c'+i,v])));
    const queryId=section.id==='replication' ? ['comparison','summary'][tableIndex] : section.id==='extension'?'extension':'sensitivity';
    const original=snapshot.queries[queryId].rows.filter(r=>section.id==='extension'?r.period==='full':section.id==='validation'?r.variant!=='ex_micro':true);
    const id=section.id+':table-'+tableIndex++;
    return <DataComponent key={index} id={id} queryId={queryId} title={queryId==='summary'?'Monthly means and annual volatility':queryId==='comparison'?'Matched-month benchmark comparison':queryId==='extension'?'Full-sample microcap results':'Construction sensitivities'} kind="table" sourceRows={original} displayRows={rows}>
      <DataTable rows={rows} columns={columns} searchable={false} compactNumbers={false} caption={section.title} />
    </DataComponent>;
  });
}

export function ReportContent(){
  const {snapshot,appTitle,setAppTitle,canEdit,mode,visible}=useDataApp();
  return <article className="report-content" aria-label="FF93 replication report">
    <header className="report-hero">
      <h1 data-data-app-title contentEditable={canEdit&&mode==='edit'} suppressContentEditableWarning onBlur={e=>{if(canEdit&&mode==='edit')setAppTitle(e.currentTarget.textContent.trim()||appTitle)}}>{appTitle}</h1>
      <RichNarrative id="report:course" value="ECON6067 Final Project · Finalized 9 October 2026 · Evidence through December 2025" label="Edit course context" />
    </header>
    {snapshot.reportSections.map(section=>visible(section.id)&&<section key={section.id} className="report-section">
      {section.queries.length ? <ReportSection id={section.id} title={section.title} queryId={section.queries[0]} queryIds={section.queries} sourceRowsByQuery={Object.fromEntries(section.queries.map(q=>[q,snapshot.queries[q].rows]))} showHeading={false}>
        <NarrativeParts section={section} snapshot={snapshot}/>
      </ReportSection> : <NarrativeParts section={section} snapshot={snapshot}/>}
      {section.charts.map(q=><EvidenceChart key={q} id={'chart-'+q} queryId={q} title={chartTitles[q]} rows={snapshot.queries[q].rows} sourceRows={snapshot.queries[q].rows} height={330}
        description="Compounded factor index (%); matched months. Gross theoretical index, not investable wealth. Vertical scales differ across factors."
        spec={{type:'line',x:'date',y:'index_pct',series:'series',yLabel:'Index change (%)',stackable:false,valueDecimals:2,colors:{Reconstructed:'#126782','French benchmark':'#e58f29',Baseline:'#126782','Exclude microcaps':'#e58f29'}}}/>)}
    </section>)}
  </article>;
}
