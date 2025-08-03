import React, { useEffect, useRef, useState } from 'react';

import useMaterial3DCore from '../hooks/core';
// import { TrajAnimation } from '../traj-animation';
import { useSubjectState } from '../hooks/useSubjectState';
import { Color } from 'dpmol';

import styles from './index.module.less';
// import { useMaterialApp } from '../../context';
import { useButtonControlStore } from '../store/buttonControlStore';
import { Ligand } from '../types';
import { useHoverAtom } from '../hooks/useHoverAtom';
import useMaterial3DState from '../hooks/useGetState';
import { MaterialCore } from '../hooks/coreMethod'
import { api } from '@/api/client'

const colorHexToNumber = (hex: any) => {
    return parseInt(hex.replace('#', ''), 16);
};

export const MaterialView: React.FC = React.memo(function MaterialView(props: any) {
    const { data, format, setKey } = props;
    const domRef = useRef<HTMLDivElement>(null);
    const [ligands, setLigands] = useState<Ligand[]>([]);

    // const { openFile } = useMaterialApp();
    const { initPlugin, lightPluginRef, coreChangeSubjectRef, isTrajSubjectRef, render } = useMaterial3DCore();
    const { getLigands } = useMaterial3DState();
    const { hoverAtom, subscribeHoverEvent } = useHoverAtom();
    // const { bindCopyEvent } = useCopyAtom();
    const isTraj = useSubjectState(isTrajSubjectRef.current);
    const { customizedUnit, color } = useButtonControlStore();


    const init = async (data: any, format: any) => {

        const res =  await api.getASEByFileReq({
            fileContent: data || '',
            format: format
        })
        const core = new MaterialCore();
        core.setByASE(res.data[0]);


        const representation = lightPluginRef.current?.managers.representation;
        // TODO: 轨迹不要化学键
        if (representation) {
            representation.hideBond = format === 'dump';
        }
        // formatSubjectRef.current.next(format);
        await render(core, {
            format,
            changeFile: false,
            autoLockCamera: false,
            changeCore: true,
            changeHistory: true,
        });
    }
    window.lightPlugin = lightPluginRef.current;
    setKey(lightPluginRef);

    useEffect(() => {
        // lightPluginRef.current&&lightPluginRef.current.layout?.canvas.remove();
        // lightPluginRef.current&&lightPluginRef.current.dispose();
        // lightPluginRef.current&&lightPluginRef.current!.clear()
        // if(!isPluginInitialized.current){
            const dispose = initPlugin(domRef.current!);
            // const subscription = coreChangeSubjectRef.current.subscribe(async () => {
            //     setLigands((await getLigands()) || []);
            // });

            // const unsubscribeHoverEvent = subscribeHoverEvent();
            // const unbindCopyEvent = bindCopyEvent();
            // if (lightPluginRef.current && lightPluginRef.current.canvas3d)
            //     lightPluginRef.current.canvas3d.camera.allowChangeClip = false;

            // const path = window.location.search.match(/path=([^&]*)/)?.[1] ?? '';
            // const projectId = window.location.search.match(/projectId=([^&]*)/)?.[1] ?? '';

            // if (path) {
            //     openFile({ path: decodeURIComponent(path), projectId: projectId ? +projectId : undefined });
            // }
            // init(data, format);
            // isPluginInitialized.current = true
            return () => {
                // subscription?.unsubscribe();
                // unsubscribeHoverEvent();
                // unbindCopyEvent();

                dispose();
            };
        
    }, []);
    useEffect(() => {
        init(data, format);
    },[data, format])

    useEffect(() => {
        lightPluginRef.current?.refresh?.();
    }, [isTraj]);

    useEffect(() => {
        lightPluginRef.current?.canvas3d?.setProps({
            renderer: {
                backgroundColor: Color(colorHexToNumber(color)),
            },
        });
    }, [color]);

    return (
        <div className={styles.view}>
            <div
                ref={domRef}
                className={styles['view-dom']}
                style={{
                    height: isTraj ? `calc(100% - 62px)` : '100%',
                }}
            />
            <div className={styles.ligands} style={customizedUnit ? {} : { marginTop: 50 }}>
                {ligands.map(({ element, color }) => (
                    <div key={element} className="ml-12 flex items-center">
                        <span
                            style={{
                                background: color,
                                width: 14,
                                height: 14,
                                borderRadius: '50%',
                            }}
                        ></span>
                        <span className="ml-8">{element}</span>
                    </div>
                ))}
            </div>
            {/* <TrajAnimation /> */}
            {!!hoverAtom && (
                <div
                    className={styles['hover-atom']}
                    style={{
                        top: hoverAtom.page?.[1],
                        left: hoverAtom.page?.[0],
                    }}
                >
                    <span>
                        {hoverAtom?.element}
                        {hoverAtom?.index + 1}{' '}
                    </span>
                    <span>(</span>
                    <span>{hoverAtom?.x?.toFixed(2)}</span>
                    <span>, </span>
                    <span>{hoverAtom?.y?.toFixed(2)}</span>
                    <span>, </span>
                    <span>{hoverAtom?.z?.toFixed(2)}</span>
                    <span>)</span>
                </div>
            )}
        </div>
    );
});
