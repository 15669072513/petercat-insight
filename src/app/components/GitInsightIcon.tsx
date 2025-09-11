import Lottie from 'lottie-react';
import React, { useMemo } from 'react';

import Commit from './commit.json';
import Fork from './fork.json';
import Star from './star.json';

interface GitInsightIconProps {
  type?: 'fork' | 'commit' | 'star';
}

const GitInsightIcon: React.FC<GitInsightIconProps> = (props) => {
  const { type } = props;

  const animationData = useMemo(() => {
    if (type === 'fork') {
      return JSON.parse(JSON.stringify(Fork)); // 转换为可扩展对象
    }
    if (type === 'commit') {
      return JSON.parse(JSON.stringify(Commit));
    }
    return JSON.parse(JSON.stringify(Star));
  }, [type]);

  return (
      <div>
        <Lottie
            style={{
              width: 'auto',
              height: '68px',
            }}
            animationData={animationData}
            autoplay={true}
            loop={false}
        />
      </div>
  );
};

export default GitInsightIcon;
