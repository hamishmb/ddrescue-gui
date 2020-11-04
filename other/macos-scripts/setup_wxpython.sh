#!/bin/bash
cd ../../dist/DDRescue_GUI.app/Contents/Resources/lib/python3.8/lib-dynload/wx
ln -s ../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib ./
ln -s ../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib ./
ln -s ../../../../../Frameworks/libwx_osx_cocoau_adv-3.1.4.0.0.dylib ./
ln -s ../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib ./
ln -s ../../../../../Frameworks/libwx_osx_cocoau_stc-3.1.4.0.0.dylib ./
cd -
