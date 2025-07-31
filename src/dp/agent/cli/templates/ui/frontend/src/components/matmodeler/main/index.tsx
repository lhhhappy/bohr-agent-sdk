import clsx from 'clsx';
// import { Spin } from 'dptd';
import React, { useState } from 'react';

// import { useSubjectState } from '../hooks/useSubjectState';
// import { useMaterialApp } from '../../context';
import { MaterialToolbar } from '../toolbar';
import { MaterialView } from './view';

import styles from './index.module.less';

interface MaterialMainProps {
    name?: string;
    children?: React.ReactNode;
    data: any;
    format: string;
}

export const MaterialMain: React.FC<MaterialMainProps> = React.memo(function MaterialMain({data, format, children }) {
    // const { loadingRef } = useMaterialApp();
    // const isLoading = useSubjectState(loadingRef.current);
    const [uniqueId,setUniqueId] = useState(0);
    return (
        <>
            {/* <Spin spinning={isLoading} fullscreen /> */}
            <div className={clsx(styles.main, 'flex-1')}>
                <div className="flex-1">
                    <MaterialToolbar uniqueId={uniqueId}/>
                    <div className={styles['view-container']}>
                        <MaterialView data={data} format={format} setKey={setUniqueId} />
                    </div>
                </div>
                {children ? <div className={styles.right}>{children}</div> : null}
            </div>
        </>
    );
});
