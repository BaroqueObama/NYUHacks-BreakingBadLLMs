import streamlit as st
import streamlit_toggle as tog

tog.st_toggle_switch(label="Label", 
                    key="Key1", 
                    default_value=False, 
                    label_after = False, 
                    inactive_color = '#D3D3D3', 
                    active_color="#11567f", 
                    track_color="#29B5E8"
                    )

print(tog)