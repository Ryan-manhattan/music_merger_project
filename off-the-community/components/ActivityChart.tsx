import React from 'react';
import { BarChart, Bar, ResponsiveContainer, XAxis, Tooltip } from 'recharts';

const data = [
  { name: 'Mon', val: 40 },
  { name: 'Tue', val: 30 },
  { name: 'Wed', val: 70 },
  { name: 'Thu', val: 50 },
  { name: 'Fri', val: 90 },
  { name: 'Sat', val: 65 },
  { name: 'Sun', val: 85 },
];

const ActivityChart: React.FC = () => {
  return (
    <div className="h-full w-full flex flex-col">
      <div className="flex justify-between items-end mb-4 px-2">
         <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Activity Pulse</h3>
            <p className="text-[10px] text-zinc-500 font-mono">Last 7 Days</p>
         </div>
         <div className="text-xs font-mono text-emerald-500">+12.4%</div>
      </div>
      <div className="flex-1 min-h-[100px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <Tooltip 
              cursor={{fill: '#27272a'}}
              contentStyle={{ backgroundColor: '#09090b', border: '1px solid #27272a', fontSize: '12px' }}
              itemStyle={{ color: '#fff' }}
            />
            <Bar dataKey="val" fill="#3f3f46" radius={[2, 2, 0, 0]} activeBar={{ fill: '#fafafa' }} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ActivityChart;